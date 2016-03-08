from django import forms
from eveonline.models import EVEApiKeyPair

class ApiAddForm(forms.Form):

    id = forms.IntegerField(min_value=1, label="API ID", required=True)
    vcode = forms.CharField(max_length=254, label="API VCode", required=True)

    def clean_id(self):
        try:
            id = int(self.cleaned_data['id'])
            return self.cleaned_data['id']
        except:
            raise forms.ValidationError("ID must be an integer")

    def clean(self):
        model = EVEApiKeyPair()
        model.id = self.cleaned_data['id']
        model.vcode = self.cleaned_data['vcode']
        if not model.validate():
            raise forms.ValidationError("API key is not valid.")
        return self.cleaned_data
