from django.shortcuts import render
from django.contrib.auth import authenticate, login

# Create your views here.
def sso_login(request):
    code = request.GET['code']
    state = request.GET['state']
    user = authenticate(code)
    if user is not None:
        if user.is_active:
            login(request, user)
            return HttpResponseRedirect("/dashboard")
        else:
            #redirect to disabled account page
            pass
    else:
        #return to login failed page
        pass

def dashboard_view(request):
    return render(request, 'dashboard.html')

def login_view(request):
    return render(request, 'login.html')
