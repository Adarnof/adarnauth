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
import openfire.views
import mumble.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # authentication
    url(r'^$', authentication.views.profile_view, name='auth_profile'),
    url(r'^login/$', authentication.views.login_view, name='auth_login_user'),
    url(r'^logout/$', authentication.views.logout_view, name='auth_logout_user'),
    url(r'^callback/$', authentication.views.sso_login),

    # groupmanagement
    url(r'^groups/$', groupmanagement.views.group_list, name='groupmanagement_group_list'),
    url(r'^groups/create/$', groupmanagement.views.group_create, name='groupmanagement_group_create'),
    url(r'^groups/manage/$', groupmanagement.views.group_list_management, name='groupmanagement_group_list_management'),
    url(r'^groups/manage/(\d*)/$', groupmanagement.views.group_manage, name='groupmanagement_group_manage'),
    url(r'^groups/manage/(\d*)/edit/$', groupmanagement.views.group_edit, name='groupmanagement_group_edit'),
    url(r'^groups/manage/(\d*)/transfer/$', groupmanagement.views.group_transfer_ownership, name='groupmanagement_group_transfer_ownership'),
    url(r'^groups/manage/(\d*)/delete/$', groupmanagement.views.group_delete, name='groupmanagement_group_delete'),
    url(r'^groups/(\d*)/apply/$', groupmanagement.views.group_application_create, name='groupmanagement_group_application_create'),
    url(r'^groups/manage/(\d*)/promote/(\d*)/$', groupmanagement.views.group_promote_member, name='groupmanagement_group_promote_member'),
    url(r'^groups/manage/(\d*)/demote/(\d*)/$', groupmanagement.views.group_demote_admin, name='groupmanagement_group_demote_admin'),
    url(r'^groups/manage/(\d*)/kick/(\d*)/$', groupmanagement.views.group_remove_member, name='groupmanagement_group_remove_member'),
    url(r'^groups/(\d*)/leave/$', groupmanagement.views.group_leave, name='groupmanagement_group_leave'),
    url(r'^groups/applications/(\d*)/accept/$', groupmanagement.views.group_application_accept, name='groupmanagement_group_application_accept'),
    url(r'^groups/applications/(\d*)/reject/$', groupmanagement.views.group_application_reject, name='groupmanagement_group_application_reject'),
    url(r'^groups/applications/(\d*)/delete/$', groupmanagement.views.group_application_delete, name='groupmanagement_group_application_delete'),
    url(r'^groups/auto/add/$', groupmanagement.views.auto_group_add, name='groupmanagement_auto_group_add'),
    url(r'^groups/auto/(\d*)/view/$', groupmanagement.views.auto_group_view, name='groupmanagement_auto_group_view'),
    url(r'^groups/auto/(\d*)/delete/$', groupmanagement.views.auto_group_delete, name='groupmanagement_auto_group_delete'),

    # access
    url(r'^access/user/(\d*)/$', access.views.list_useraccess, name='access_list_useraccess'),
    url(r'^access/(\d*)/recheck/$', access.views.recheck_access, name='access_recheck_useraccess'),
    url(r'^access/rules/$', access.views.list_access_rules, name='access_list_access_rules'),
    url(r'^access/rules/character/add/$', access.views.characteraccess_create, name='access_characteraccess_create'),
    url(r'^access/rules/character/(\d*)/delete/$', access.views.characteraccess_delete, name='access_characteraccess_delete'),
    url(r'^access/rules/character/(\d*)/view/$', access.views.view_character_access, name='access_view_character_access'),
    url(r'^access/rules/corp/add/$', access.views.corpaccess_create, name='access_corpaccess_create'),
    url(r'^access/rules/corp/(\d*)/delete/$', access.views.corpaccess_delete, name='access_corpaccess_delete'),
    url(r'^access/rules/corp/(\d*)/view/$', access.views.view_corp_access, name='access_view_corp_access'),
    url(r'^access/rules/alliance/add/$', access.views.allianceaccess_create, name='access_allianceaccess_create'),
    url(r'^access/rules/alliance/(\d*)/delete/$', access.views.allianceaccess_delete, name='access_allianceaccess_delete'),
    url(r'^access/rules/alliance/(\d*)/view/$', access.views.view_alliance_access, name='access_view_alliance_access'),

    # eveonline
    url(r'^characters/api/add/$', eveonline.views.api_key_add, name='eveonline_api_key_add'),
    url(r'^characters/api/(\d*)/delete/$', eveonline.views.api_key_delete, name='eveonline_api_key_delete'),
    url(r'^characters/api/(\d*)/update/$', eveonline.views.api_key_update, name='eveonline_api_key_update'),
    url(r'^characters/api/(\d*)/verify/$', eveonline.views.api_key_verify, name='eveonline_api_key_verify'),

    # openfire
    url(r'^openfire/$', openfire.views.openfireservice_list, name='openfire_service_list'),
    url(r'^openfire/add/$', openfire.views.openfireservice_add, name='openfire_service_add'),
    url(r'^openfire/(\d*)/edit/$', openfire.views.openfireservice_change, name='openfire_service_edit'),
    url(r'^openfire/(\d*)/delete/$', openfire.views.openfireservice_delete, name='openfire_service_delete'),

    # mumble
    url(r'^mumble/$', mumble.views.mumble_list, name='mumble_list'),
    url(r'^mumble/(\d*)/activate/$', mumble.views.mumble_activate, name='mumble_activate'),
    url(r'^mumble/(\d*)/password/$', mumble.views.mumble_password, name='mumble_password'),
    url(r'^mumble/(\d*)/deactivate/$', mumble.views.mumble_deactivate, name='mumble_deactivate'),
]
