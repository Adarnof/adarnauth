from django.contrib import admin
from django import forms
from models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule, StandingAccessRule

class UserAccessForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserAccessForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['object_id'].widget.attrs['readonly'] = True
    def clean_user(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['user'] != instance.user:
                self.data['user'] = instance.user
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.user
        return self.cleaned_data['user']
    def clean_character(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['character'] != instance.character:
                self.data['character'] = instance.character
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.character
        return self.cleaned_data['character']
    def clean_content_type(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['content_type'] != instance.content_type:
                self.data['content_type'] = instance.content_type
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.content_type
        return self.cleaned_data['content_type']
    def clean_object_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.object_id
        return self.cleaned_data['object_id']

@admin.register(UserAccess)
class UserAccessAdmin(admin.ModelAdmin):
    form = UserAccessForm

admin.site.register(CharacterAccessRule)
admin.site.register(CorpAccessRule)
admin.site.register(AllianceAccessRule)
admin.site.register(StandingAccessRule)
