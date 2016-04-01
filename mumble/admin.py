from django.contrib import admin
from django import forms
from .models import MumbleUser, MumbleGroup, MumbleService

class MumbleGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(MumbleGroupForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['service'].widget.attrs['disabled'] = True

    def clean_group_name(self):
        return self.cleaned_data['service']._sanatize_username(self.cleaned_data['group_name'])

    def clean_service(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['service'] != instance.service:
                self.data['service'] = instance.service
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.service
        return self.cleaned_data['service']

@admin.register(MumbleGroup)
class MumbleGroupAdmin(admin.ModelAdmin):
    form = MumbleGroupForm

class MumbleUserForm(forms.ModelForm):
    groups = forms.CharField(widget=forms.Textarea(attrs={'readonly': True}), required=False)

    class Meta:
        exclude = ['mumble_groups']

    def __init__(self, *args, **kwargs):
        super(MumbleUserForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['user'].widget.attrs['disabled'] = True
            self.fields['service'].widget.attrs['disabled'] = True
        if instance:
            gs = ""
            for g in instance.mumble_groups.all():
                gs = gs + str(g) + "\n"
            self.fields['groups'].initial = gs.strip("\n")

    def clean_user(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['user'] != instance.user:
                self.data['user'] = instance.user
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.user
        return self.cleaned_data['user']

    def clean_service(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['service'] != instance.service:
                self.data['service'] = instance.service
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.service
        return self.cleaned_data['service']

    def clean_username(self):
        return self.cleaned_data['service']._sanatize_username(self.cleaned_data['username'])

@admin.register(MumbleUser)
class MumbleUserAdmin(admin.ModelAdmin):
    form = MumbleUserForm

admin.site.register(MumbleService)
