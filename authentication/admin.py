from django.contrib import admin
from django import forms
from models import User
from eveonline.models import EVECharacter

class UserForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['password'].required = False
        if instance and instance.pk:
            self.fields['main_character_id'].widget.attrs['readonly'] = True

    def clean_main_character_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['main_character_id'] != instance.main_character_id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.main_character_id
        else:
            if EVECharacter.objects.check_id(self.cleaned_data['main_character_id']):
                return self.cleaned_data['main_character_id']
            else:
                raise forms.ValidationError("Failed to verify via API")

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    form = UserForm

    def save_model(self, request, obj, form, change):
        if not change:
            user = User.objects.create_user(form.cleaned_data['main_character_id'])
        super(UserAdmin, self).save_model(request, obj, form, change)
            
