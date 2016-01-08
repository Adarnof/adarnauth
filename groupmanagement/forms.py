from django import forms
from .models import ExtendedGroup

class GroupAddForm(forms.Form):
    name = forms.CharField(max_length=254, label='Group Name', required=True)
    description = forms.CharField(max_length=254, label='Description', required=True)
    hidden = forms.BooleanField(required=False, label='Hidden', initial=False)
    applications = forms.BooleanField(required=False, initial=False, label='Require Application to Join')

    def clean_name(self):
        if ExtendedGroup.objects.filter(group__name=self.cleaned_data['name']).exists():
            raise forms.ValidationError("Group with that name already exists")
        return self.cleaned_data['name']

    def __init__(self, user=None, *args, **kwargs):
        super(GroupAddForm, self).__init__(*args, **kwargs)
        choices = []
        if user:
            for g in ExtendedGroup.objects.all():
                if g.owner == user or user in g.admins.all():
                    choices.append(g, str(g)))
        parent = models.ChoiceField(choices=choices, label='Parent Group', blank=True)

class GroupEditForm(forms.Form):
    description = forms.CharField(max_length=254, label='Description', required=True)
    hidden = forms.BooleanField(required=False, initial=False, label='Hidden')
    applications = forms.BooleanField(required=False, initial=False, label='Require Application to Join')
    def __init__(self, user=None, *args, **kwargs):
        super(GroupCreateForm, self).__init__(*args, **kwargs)
        choices = []
        if user:
            for g in ExtendedGroup.objects.all():
                if g.owner == user or user in g.admins.all():
                    choices.append(g, str(g)))
        parent = models.ChoiceField(choices=choices, label='Parent Group', blank=True)

class GroupTransferForm(forms.Form):
    def __init__(self, exgroup, *args, **kwargs):
        super(GroupTransferForm, self).__init__(*args, **kwargs)
        choices = []
        for a in exgroup.admins.all():
            choices.append(a, str(a)))
        owner = models.ChoiceField(choices=choices, label='New Owner', required=True)
