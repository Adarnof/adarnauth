from django.contrib import admin
from models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule

admin.site.register(UserAccess)
admin.site.register(CharacterAccessRule)
admin.site.register(CorpAccessRule)
admin.site.register(AllianceAccessRule)
