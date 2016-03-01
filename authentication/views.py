from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Create your views here.
def sso_login(request):
    code = request.GET['code']
    state = request.GET['state']
    logger.debug("SSO redirect received for state %s with code %s" % (state, code))
    if state=='login':
        user = authenticate(code=code)
        if user is not None:
            if user.is_active:
                login(request, user)
                logger.info("Login succesful for %s" % user)
                return redirect('auth_dashboard')
            else:
                #redirect to disabled account page
                logger.info("Login unsuccesful for %s: account marked inactive." % user)
                return redirect('auth_login_user')
        else:
            #return to login failed page
            logger.info("Login unsuccesful: no user model returned.")
            return redirect('auth_login_user')
    else:
        logger.debug("State %s not implemented." % state)
        return redirect('auth_login_user')

def dashboard_view(request):
    return render(request, 'registered/authentication/dashboard.html')

def login_view(request):
    return render(request, 'public/login.html', {'sso_callback_uri':settings.SSO_CALLBACK_URI, 'sso_client_id':settings.SSO_CLIENT_ID})

def logout_view(request):
    logout(request)
    return redirect('auth_dashboard')

def landing_view(request):
    return render(request, 'public/landing.html')
