from django.contrib import admin
from models import EVECharacter, EVECorporation, EVEAlliance

# Register your models here.
admin.site.register(EVECharacter)
admin.site.register(EVECorporation)
admin.site.register(EVEAlliance)
