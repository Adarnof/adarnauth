from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import logging
from django.conf import settings
from eve_sso.decorators import token_required

logger = logging.getLogger(__name__)

@token_required(new=True)
def login_view(request, tokens):
    logger.debug('sso_login called')
    token = tokens[0]
    user = authenticate(token=token)
    token.delete()
    if user:
        if user.is_active:
            login(request, user)
            return redirect(request.GET.get('next', '/'))
    raise Exception

def logout_view(request):
    logout(request)
    return redirect('auth_profile')

@login_required
def profile_view(request):
    logger.debug("profile_view called by user %s" % request.user)
    main = request.user.main_character
    apis = request.user.eveapikeypair_set.all()
    orphans = []
    unclaimed = set([])
    for char in request.user.characters.all():
        if char.apis.all().exists():
            for api in char.apis.filter(owner__isnull=True):
                unclaimed.add(api)
        else:
            orphans.append(char)
    contested = set([])
    for api in apis:
        for char in api.characters.exclude(user=request.user):
            if User.objects.filter(main_character_id=char.id).exists():
                char_main = User.objects.get(main_character_id=char.id)
            else:
                char_main = None
            contested.add((char, char_main))
    ua = request.user.useraccess_set.all()
    logger.debug("Retrieved %s apis with %s orphans %s contested and %s unclaimed for %s" % (len(apis), len(orphans), len(contested), len(unclaimed), request.user))
    context = {
        'main': main,
        'apis': apis,
        'orphans': orphans,
        'useraccess': ua,
        'contested': contested,
        'unclaimed': unclaimed,
    }
    return render(request, 'registered/authentication/profile.html', context)
