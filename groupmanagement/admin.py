from django.contrib import admin
from .models import ExtendedGroup, GroupApplication, AutoGroup

admin.site.register(ExtendedGroup)
admin.site.register(GroupApplication)
admin.site.register(AutoGroup)
