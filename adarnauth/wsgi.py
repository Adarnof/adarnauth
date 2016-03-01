"""
WSGI config for adarnauth project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "adarnauth.settings")

# virtualenv wrapper
activate_env=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

application = get_wsgi_application()
