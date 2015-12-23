from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect

# Create your views here.
def sso_login(request):
    code = request.GET['code']
    state = request.GET['state']
    user = authenticate(code=code)
    if user is not None:
        if user.is_active:
            login(request, user)
            return HttpResponseRedirect("/dashboard")
        else:
            #redirect to disabled account page
            return HttpResponseRedirect("/login")
    else:
        #return to login failed page
        return HttpResponseRedirect("/login")

def dashboard_view(request):
    return render(request, 'dashboard.html')

def login_view(request):
    return render(request, 'login.html')
