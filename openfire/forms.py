from django import forms
from .models import OpenfireService

class OpenfireServiceAddForm(forms.Form):
    name = models.CharField(max_length=254, label="Service Name", required=True)
    address = models.CharField(max_length=254, label="Web Address", required=True)
    port = models.IntegerField(min_value=1, max_value=65535, label="Port", required=True)
    restapi_address = models.CharField(max_length=254, label="RESTAPI Plugin Address", required=True)
    restapi_secret_key = models.CharField(max_length=254, label="RESTAPI Plugin Secret Key", required=True)

    def clean(self):
        super(OpenfireServiceAddForm, self).clean()
        test = OpenfireService()
        test.restapi_address = self.cleaned_data['restapi_address']
        test.restapi_secret_key = self.cleaned_data['restapi_secret_key']
        if not test.test_connection():
            raise forms.ValidationError("Unable to connect to REST API service.")
        return self.cleaned_data
