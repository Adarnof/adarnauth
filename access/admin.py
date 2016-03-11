from django.contrib import admin
from models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule, StandingAccessRule

admin.site.register(UserAccess)
admin.site.register(CharacterAccessRule)
admin.site.register(CorpAccessRule)
admin.site.register(AllianceAccessRule)
admin.site.register(StandingAccessRule)
