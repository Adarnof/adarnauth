from django import forms
from .models import ExtendedGroup

class GroupAddForm(forms.Form):
    name = forms.CharField(max_length=254, label='Group Name', required=True)
    description = forms.CharField(max_length=254, label='Description', required=True)
    hidden = forms.BooleanField(required=False, label='Hidden', initial=False)
    applications = forms.BooleanField(required=False, initial=False, label='Require Application to Join')
    parent = forms.ChoiceField(choices=((None, 'None'),), label='Parent Group', required=False)

    def clean_name(self):
        if ExtendedGroup.objects.filter(group__name=self.cleaned_data['name']).exists():
            raise forms.ValidationError("Group with that name already exists")
        return self.cleaned_data['name']

class GroupEditForm(forms.Form):
    description = forms.CharField(max_length=254, label='Description', required=True)
    hidden = forms.BooleanField(required=False, initial=False, label='Hidden')
    applications = forms.BooleanField(required=False, initial=False, label='Require Application to Join')
    parent = forms.ChoiceField(choices=((None, 'None'),), label='Parent Group', required=False)

class GroupTransferForm(forms.Form):
    owner = forms.ChoiceField(label='New Owner', required=True)
