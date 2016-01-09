from django import forms
from eveonline.managers import EVEManager

class CharacterAccessForm(forms.Form):
    id = forms.IntegerField(label="Character ID", required=True, min_value=1)

    def clean_id(self):
        if not EVEManager.check_if_character_id_valid(self.cleaned_data['id']):
            raise forms.ValidationError("Supplied character ID is invalid.")
        return self.cleaned_data['id']

class CorpAccessForm(forms.Form):
    id = forms.IntegerField(label="Corp ID", required=True, min_value=1)

    def clean_id(self):
        if not EVEManager.check_if_corp_id_valid(self.cleaned_data['id']):
            raise forms.ValidationError("Supplied corp ID is invalid.")
        return self.cleaned_data['id']

class AllianceAccessForm(forms.Form):
    id = forms.IntegerField(label="Alliance ID", required=True, min_value=1)

    def clean_id(self):
        if not EVEManager.check_if_alliance_id_valid(self.cleaned_data['id']):
            raise forms.ValidationError("Supplied alliance ID is invalid.")
        return self.cleaned_data['id']

