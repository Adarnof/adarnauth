"""adarnauth URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url
from django.contrib import admin
import authentication.views
import groupmanagement.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    #SSO
    url(r'^login/$', authentication.views.login_view, name='auth_login_user'),
    url(r'^logout/$', authentication.views.logout_view, name='auth_logout_user'),
    url(r'^sso_callback/$', authentication.views.sso_login),
    url(r'^dashboard/$', authentication.views.dashboard_view, name='auth_dashboard'),

    # groupmanagement
    url(r'^groups/$', groupmanagement.views.group_list, name='groupmanagement_group_list'),
    url(r'^groups/create/$', groupmanagement.views.group_create, name='groupmanagement_group_create'),
    url(r'^groups/([0-9]*)/$', groupmanagement.views.group_manage, name='groupmanagement_group_manage'),
    url(r'^groups/([0-9]*)/edit/$', groupmanagement.views.group_edit, name='groupmanagement_group_edit'),
    url(r'^groups/([0-9]*)/transfer/$', groupmanagement.views.group_transfer_ownership, name='groupmanagement_group_transfer_ownership'),
]
