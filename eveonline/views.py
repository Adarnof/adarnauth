from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from forms import ApiAddForm
from models import EVEApiKeyPair, EVECharacter
from authentication.models import User, CallbackRedirect
from authentication.tasks import get_character_id_from_sso_code
from django.core.urlresolvers import reverse
import logging

logger = logging.getLogger(__name__)

@login_required
def api_key_add(request):
    logger.debug("api_key_add called by user %s" % request.user)
    if request.method=='POST':
        form = ApiAddForm(request.POST)
        logger.debug("Request type POST, contains form, is valid: %s" % form.is_valid())
        if form.is_valid():
            id = form.cleaned_data['id']
            vcode = form.cleaned_data['vcode']
            if EVEApiKeyPair.objects.filter(id=id).exists():
                if EVEApiKeyPair.objects.filter(id=id).filter(owner__isnull=True).exists():
                    logger.info("User %s entered existing key %s missing owner - redirecting to SSO verification" % (request.user, EVEApiKeyPair.objects.get(id=id)))
                    return redirect(api_key_verify, id)
                else:
                    logger.warn("User %s attempting to duplicate %s" % (request.user, EVEApiKeyPair.objects.get(id=id)))
                    form.add_error(None, 'Key with ID %s already claimed')
            else:
                api = EVEApiKeyPair(id=id, vcode=vcode)
                logger.info("User %s creating %s" % (request.user, api))
                api.save()
                return redirect(api_key_verify, api.id)
        else:
             logger.debug("User %s ApiAddForm failed validation." % request.user)
    else:
        form = ApiAddForm()
    context = {
        'form': form,
        'title': 'Add API Key',
        'button_text': 'Add',
    }
    return render(request, 'public/form.html', context=context)

@login_required
def api_key_delete(request, api_id):
    logger.debug("api_key_delete called by user %s for api id %s" % (request.user, api_id))
    api = get_object_or_404(EVEApiKeyPair, id=api_id)
    if api.owner == request.user:
        logger.info("User %s deleting %s" % (request.user, api))
        api.delete()
    else:
        logger.warn("User %s not eligible to delete %s" % (request.user, api))
    return redirect('auth_profile')

@login_required
def api_key_update(request, api_id):
    logger.debug("api_key_update called by user %s for api id %s" % (request.user, api_id))
    api = get_object_or_404(EVEApiKeyPair, id=api_id)
    if api.owner == request.user:
        logger.info("User %s updating %s" % (request.user, api))
        api.update()
    else:
        logger.warn("User %s not eligible to update %s" % (request.user, api))
    return redirect('auth_profile')

@login_required
def api_key_verify(request, api_id):
    logger.debug("api_key_verify called by user %s for api_id %s" % (request.user, api_id))
    api = get_object_or_404(EVEApiKeyPair, id=api_id)
    if request.method == 'POST':
        code = request.get['code']
        if CallbackRedirect.objects.filter(session__session_key=request.session.session_key).filter(action='verify').exists():
            model = CallbackRedirect.objects.get(session__session_key=request.session.session_key, action='verify')
            if model.validate(request):
                character_id = get_character_id_from_sso_code(code)
                if character_id:
                    if api.characters.filter(id=character_id).exists():
                        logger.info("User %s verified %s via SSO" % (request.user, api))
                        api.owner = request.user
                        api.save(update_fields=['user'])
                    else:
                        logger.warn("User %s failed to verify %s via SSO: authorized character not found on key" % (request.user, api))
                else:
                    logger.warn("User %s failed to verify %s via SSO: failed to retrieve character id from code exchange" % (request.user, api))
            else:
                logger.warn("Failed to validate SSO callback for user %s verification of %s" % (request.user, api))
        else:
            logger.warn("Failed to locate CallbackRedirect for user %s verification of %s" % (request.user, api))
        return redirect('auth_profile')
    else:
        if CallbackRedirect.objects.filter(session__session_key=request.session.session_key).exists():
            model = CallbackRedirect.objects.get(session__session_key=request.session.session_key)
            if model.action != 'verify':
                model.action = 'verify'
                model.save()
        else:
            url = reverse(api_key_verify, args=api_id)
            request.GET['next'] = url
            model = CallbackRedirect()
            model.populate(request)
            model.action = "verify"
            model.save()
        return render(request, 'public/login.html', {'state': model.hash})
