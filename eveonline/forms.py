from django import forms
from eveonline.managers import EVEApiManager

class ApiAddForm(forms.Form):
    id = forms.IntegerField(min_value=1, label="API ID", required=True)
    vcode = forms.CharField(max_length=254, label="API VCode", required=True)
    def clean(self):
        if EVEApiManager.check_api_key_is_valid(self.cleaned_data['id'], self.cleaned_data['vcode']) is not True:
            raise forms.ValidationError("API key is not valid.")
        return self.cleaned_data
