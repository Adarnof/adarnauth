from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from .forms import ApiAddForm
from .models import EVEApiKeyPair, EVECharacter
from authentication.models import User
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
            api = EVEApiKeyPair(id=id, vcode=vcode, owner=request.user)
            logger.info("User %s creating %s" % (request.user, api))
            api.save()
            return redirect('eveonline_character_list')
        else:
             logger.warn("User %s ApiAddForm failed validation." % request.user)
    else:
        form = ApiAddForm()
    return render(request, 'registered/eveonline/apiaddform.html', context={'form':form})

@login_required
def api_key_delete(request, api_id):
    logger.debug("api_key_delete called by user %s for api id %s" % (request.user, api_id))
    api = get_object_or_404(EVEApiKeyPair, id=api_id)
    if api.owner == request.user:
        logger.info("User %s deleting %s" % (request.user, api))
        api.delete()
    else:
        logger.warn("User %s not eligible to delete %s" % (request.user, api))
    return redirect('eveonline_character_list')

@login_required
def api_key_update(request, api_id):
    logger.debug("api_key_update called by user %s for api id %s" % (request.user, api_id))
    api = get_object_or_404(EVEApiKeyPair, id=api_id)
    if api.owner == request.user:
        logger.info("User %s updating %s" % (request.user, api))
        api.update()
    else:
        logger.warn("User %s not eligible to update %s" % (request.user, api))
    return redirect('eveonline_character_list')

@login_required
def character_list(request):
    logger.debug("character_list called by user %s" % request.user)
    main = request.user.main_character
    if not main:
        logger.error("User %s missing main character model." % request.user)
    apis = EVEApiKeyPair.objects.filter(owner=request.user)
    orphans = []
    for char in request.user.characters.all():
        if char.apis.all().exists() is not True:
            orphans.append(char)
    valid = 0
    invalid = 0
    unverified = 0
    for api in apis:
        if api.is_valid:
            valid += 1
        elif api.is_valid==None:
            unverified += 1
        else:
            invalid += 1
    logger.debug("Collected %s apis with %s orphans for user %s" % (len(apis), len(orphans), request.user))
    context = {
        'main': main,
        'apis': apis,
        'orphans': orphans,
        'valid': valid,
        'invalid': invalid,
        'unverified': unverified,
    }
    return render(request, 'registered/eveonline/characterlist.html', context=context)
