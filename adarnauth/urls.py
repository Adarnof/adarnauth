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
import access.views
import eveonline.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # authentication
    url(r'^$', authentication.views.landing_view, name='auth_landing'),
    url(r'^login/$', authentication.views.login_view, name='auth_login_user'),
    url(r'^logout/$', authentication.views.logout_view, name='auth_logout_user'),
    url(r'^callback/$', authentication.views.sso_login),
    url(r'^dashboard/$', authentication.views.dashboard_view, name='auth_dashboard'),

    # groupmanagement
    url(r'^groups/$', groupmanagement.views.group_list, name='groupmanagement_group_list'),
    url(r'^groups/create/$', groupmanagement.views.group_create, name='groupmanagement_group_create'),
    url(r'^groups/manage/$', groupmanagement.views.group_list_management, name='groupmanagement_group_list_management'),
    url(r'^groups/manage/([0-9]*)/$', groupmanagement.views.group_manage, name='groupmanagement_group_manage'),
    url(r'^groups/manage/([0-9]*)/edit/$', groupmanagement.views.group_edit, name='groupmanagement_group_edit'),
    url(r'^groups/manage/([0-9]*)/transfer/$', groupmanagement.views.group_transfer_ownership, name='groupmanagement_group_transfer_ownership'),
    url(r'^groups/manage/([0-9]*)/delete/$', groupmanagement.views.group_delete, name='groupmanagement_group_delete'),
    url(r'^groups/([0-9]*)/apply/$', groupmanagement.views.group_application_create, name='groupmanagement_group_application_create'),
    url(r'^groups/manage/([0-9]*)/promote/([0-9]*)/$', groupmanagement.views.group_promote_member, name='groupmanagement_group_promote_member'),
    url(r'^groups/manage/([0-9]*)/demote/([0-9]*)/$', groupmanagement.views.group_demote_admin, name='groupmanagement_group_demote_admin'),
    url(r'^groups/manage/([0-9]*)/kick/([0-9]*)/$', groupmanagement.views.group_remove_member, name='groupmanagement_group_remove_member'),
    url(r'^groups/([0-9]*)/leave/$', groupmanagement.views.group_leave, name='groupmanagement_group_leave'),
    url(r'^groups/applications/([0-9]*)/accept/$', groupmanagement.views.group_application_accept, name='groupmanagement_group_application_accept'),
    url(r'^groups/applications/([0-9]*)/reject/$', groupmanagement.views.group_application_reject, name='groupmanagement_group_application_reject'),
    url(r'^groups/applications/([0-9]*)/delete/$', groupmanagement.views.group_application_delete, name='groupmanagement_group_application_delete'),

    # access
    url(r'^access/$', access.views.list_useraccess, name='access_list_useraccess'),
    url(r'^access/([0-9]*)/recheck/$', access.views.recheck_access, name='access_recheck_useraccess'),
    url(r'^access/rules/$', access.views.list_access_rules, name='access_list_access_rules'),
    url(r'^access/rules/character/add/$', access.views.characteraccess_create, name='access_characteraccess_create'),
    url(r'^access/rules/character/([0-9]*)/delete/$', access.views.characteraccess_delete, name='access_characteraccess_delete'),
    url(r'^access/rules/character/([0-9]*)/view/$', access.views.view_character_access, name='access_view_character_access'),
    url(r'^access/rules/corp/add/$', access.views.corpaccess_create, name='access_corpaccess_create'),
    url(r'^access/rules/corp/([0-9]*)/delete/$', access.views.corpaccess_delete, name='access_corpaccess_delete'),
    url(r'^access/rules/corp/([0-9]*)/view/$', access.views.view_corp_access, name='access_view_corp_access'),
    url(r'^access/rules/alliance/add/$', access.views.allianceaccess_create, name='access_allianceaccess_create'),
    url(r'^access/rules/alliance/([0-9]*)/delete/$', access.views.allianceaccess_delete, name='access_allianceaccess_delete'),
    url(r'^access/rules/alliance/([0-9]*)/view/$', access.views.view_alliance_access, name='access_view_alliance_access'),

    # eveonline
    url(r'^characters/$', eveonline.views.character_list, name='eveonline_character_list'),
    url(r'^characters/api/add/$', eveonline.views.api_key_add, name='eveonline_api_key_add'),
    url(r'^characters/api/([0-9]*)/delete/$', eveonline.views.api_key_delete, name='eveonline_api_key_delete'),
    url(r'^characters/api/([0-9]*)/update/$', eveonline.views.api_key_update, name='eveonline_api_key_update'),
]
