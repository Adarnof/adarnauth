from django.contrib import admin
from django import forms
from .models import ExtendedGroup, GroupApplication, AutoGroup

class ExtendedGroupForm(forms.ModelForm):
    def clean_group(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['group'] != instance.group:
                self.data['group'] = instance.group
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.group
        return self.cleaned_data['group']

@admin.register(ExtendedGroup)
class ExtendedGroupAdmin(admin.ModelAdmin):
    form = ExtendedGroupForm

class GroupApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GroupApplicationForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['response'].widget.attrs['disabled'] = True

    def clean_user(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['user'] != instance.user:
                self.data['user'] = instance.user
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.user
        return self.cleaned_data['user']
    def clean_extended_group(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['extended_group'] != instance.extended_group:
                self.data['extended_group'] = instance.extended_group
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.extended_group
        return self.cleaned_data['extended_group']
    def clean_response(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.response
        return self.cleaned_data['response']

@admin.register(GroupApplication)
class GroupApplicationAdmin(admin.ModelAdmin):
    form = GroupApplicationForm

class AutoGroupForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AutoGroupForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['object_id'].widget.attrs['readonly'] = True
    def clean_group(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['group'] != instance.group:
                self.data['group'] = instance.group
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.group
        return self.cleaned_data['group']
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

@admin.register(AutoGroup)
class AutoGroupAdmin(admin.ModelAdmin):
    form = AutoGroupForm
