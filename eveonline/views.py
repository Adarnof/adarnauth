from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from .forms import ApiAddForm
from .models import EVEApiKeyPair, EVECharacter
from authentication.models import User
import logging

logger = logging.getLogger(__name__)

@login_required
def api_key_add(request):
    logger.debug("api_key_add called by user %s" % reques.user)
    if request.method=='POST':
        form = ApiAddForm(request.POST)
        logger.debug("Request type POST, contains form, is valid: %s" % form.is_valid())
        if form.is_valid():
            id = form.cleaned_data['id']
            vcode = form.cleaned_data['vcode']
            api = EVEApiKeyPair(id=id, vcode=vcode, owner=user)
            logger.info("User %s creating %s" % request.user, api)
            api.save(update_fields['id', 'vcode', 'owner'])
            return redirect('eveonline_character_list')
         else:
             logger.warn("User %s ApiAddForm failed validation.")
    else:
        form = ApiAddForm()
    return render(request, 'registered/eveonline/apiaddform.html', context={'form':form})

@login_required
def api_key_delete(request, api_id):
    logger.debug("api_key_delete called by user %s for api id %s" % (request.user, api_id))
    api = get_object_or_404(EVEApiKeyPair, id=api_id))
    if api.owner == request.user:
        chars = api.characters.all()
        logger.info("User %s deleting %s" % (request.user, api))
        api.delete()
        for char in chars:
            logger.debug("Validating character %s still owned via api" % char)
            for api in char.apis.all():
                if api.owner == request.user:
                    logger.debug("Character %s still owned by %s through %s" % (char, request.user, api))
                    break
            else:
                if User.objects.filter(main_character_id==char.id).exists():
                    logger.debug("Preserving character %s user as is a main." % char)
                else:
                    logger.info("Character %s no longer has verified user." % char)
                    char.user = None
                    char.save(update_fields=['user']
    else:
        logger.warn("User %s not eligible to delete %s" % (request.user, api))
    return redirect('eveonline_character_list')

@login_required
def character_list(request):
    logger.debug("character_list called by user %s" % request.user)
    main = request.user.main_character
    if not main:
        logger.error("User %s missing main character model." % request.user)
    apis = EVEApiKeyPair.objects.filter(owner=request.user)
    api_dict = {}
    for api in apis:
        chars = list(api.characters.all())
        api_dict.append(api:chars)
    orphans = []
    for char in request.user.characters.all():
        if char.apis.all().exists() is not True:
            orphans.append(char)
    logger.debug("Collected %s apis with %s orphans for user %s" % (len(api_dict), len(orphans))
    context = {
        'main': main,
        'apis': api_dict,
        'orphans': orphans,
    }
    return render(request, 'registered/eveonline/characterlist.html', context=context)
