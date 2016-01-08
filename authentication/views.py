from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def sso_login(request):
    code = request.GET['code']
    state = request.GET['state']
    logger.debug("SSO redirect received with code: " + code)
    user = authenticate(code=code)
    if user is not None:
        if user.is_active:
            login(request, user)
            logger.info("Login succesful for " + str(user))
            return HttpResponseRedirect("/dashboard")
        else:
            #redirect to disabled account page
            logger.info("Login unsuccesful for " + str(user) + ": account marked inactive.")
            return HttpResponseRedirect("/login")
    else:
        #return to login failed page
        logger.info("Login unsuccesful: no user model returned.")
        return HttpResponseRedirect("/login")

def dashboard_view(request):
    return render(request, 'dashboard.html')

def login_view(request):
    return render(request, 'login.html')

def logout_view(request):
    logout(user)
    return render(request, 'login.html')
