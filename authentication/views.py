from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import logging
from django.conf import settings
from models import CallbackRedirect, User

logger = logging.getLogger(__name__)

# Create your views here.
def sso_login(request):
    code = request.GET.get('code', None)
    state = request.GET.get('state', None)
    logger.debug("SSO redirect received for state %s with code %s" % (state, code))
    if CallbackRedirect.objects.filter(hash=state).exists():
        model = CallbackRedirect.objects.get(hash=state)
        if model.action == 'login':
            if model.validate(request):
                model.delete()
                user = authenticate(code=code)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        logger.info("Login succesful for %s" % user)
                        return redirect(model.url)
                    else:
                        #redirect to disabled account page
                        logger.info("Login unsuccesful for %s: account marked inactive." % user)
                        return redirect('auth_login_user')
                else:
                    #return to login failed page
                    logger.info("Login unsuccesful: no user model returned.")
                    return redirect('auth_login_user')
            else:
                model.delete()
                logger.warn("Failed to validate SSO callback")
                return redirect('auth_login_user')
        elif model.action == 'verify':
            return redirect(model.url + '?state=' + state + '&code=' + code)
        else:
            logger.debug("State %s not implemented." % state)
            return redirect('auth_login_user')
    else:
        logger.debug("No CallbackRedirect model found for session key %s" % request.session.session_key)
        return redirect('auth_login_user')

def login_view(request):
    if not request.session.exists(request.session.session_key):
        request.session.create() 
    if CallbackRedirect.objects.filter(session_key=request.session.session_key).exists() is False:
        model = CallbackRedirect()
        model.populate(request)
        model.save()
    else:
        model = CallbackRedirect.objects.get(session_key=request.session.session_key)
        if model.action != 'login':
            model.action = 'login'
            model.save()
    return render(request, 'public/login.html', {'title':'Login', 'state':model.hash})

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
