from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import logging
from django.conf import settings
from models import CallbackRedirect

logger = logging.getLogger(__name__)

# Create your views here.
def sso_login(request):
    code = request.GET['code']
    state = request.GET['state']
    logger.debug("SSO redirect received for state %s with code %s" % (state, code))
    if CallbackRedirect.objects.filter(session__session_key=request.session.session_key).exists():
        model = CallbackRedirect.objects.get(session__session_key=request.session.session_key)
        if model.action == 'login':
            if model.validate(request):
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
                logger.warn("Failed to validate SSO callback")
                return redirect('auth_login_user')
        else:
            logger.debug("State %s not implemented." % state)
            return redirect('auth_login_user')
    else:
        logger.debug("No CallbackRedirect model found for session key %s" % request.session.session_key)
        return redirect('auth_login_user')

def login_view(request):
    if not request.session.exists(request.session.session_key):
        request.session.create() 
    if CallbackRedirect.objects.filter(session=request.session).exists() is False:
        model = CallbackRedirect()
        model.populate(request)
        model.save()
    else:
        model = CallbackRedirect.objects.get(session=request.session)
    return render(request, 'public/login.html', {'sso_callback_uri':settings.SSO_CALLBACK_URI, 'sso_client_id':settings.SSO_CLIENT_ID, 'state':model.hash})

def logout_view(request):
    logout(request)
    return redirect('auth_profile')

@login_required
def profile_view(request):
    logger.debug("profile_view called by user %s" % request.user)
    main = request.user.main_character
    if not main:
        logger.error("User %s missing main character model." % request.user)
    apis = request.user.eveapikeypair_set.all()
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
    ua = request.user.useraccess_set.all()
    context = {
        'main': main,
        'apis': apis,
        'orphans': orphans,
        'useraccess': ua,
    }
    return render(request, 'registered/authentication/profile.html', context)
