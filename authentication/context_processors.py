from django.conf import settings

def sso(request):
    data = {
        'sso_client_id': settings.SSO_CLIENT_ID,
        'sso_callback_uri': settings.SSO_CALLBACK_URI,
        }
    return data
