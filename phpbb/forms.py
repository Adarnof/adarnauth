from django import forms
from .models import Phpbb3Service

class Phpbb3ServiceAddForm(forms.Form):
    name = forms.CharField(max_length=254, label="Service Name", required=True)
    address = forms.CharField(max_length=254, label="Web Address", required=True)
    revoked_email = forms.EmailField(max_length=254, label="Revoked Account Email", required=True)
    set_avatars = forms.BooleanField(initial=False, label="Set Character Portrait as Avatar", required=True)
    required_groups = forms.MultipleChoiceField(choices=[(None, 'None'),], label="Required Group Membership For Access", required=False)
    mysql_user = forms.CharField(max_length=254, label="MySQL User", required=True)
    mysql_password = forms.CharField(max_length=254, label="MySQL User Password", required=True)
    mysql_database_name = forms.CharField(max_length=254, label="MySQL Database Name", required=True)
    mysql_database_host = forms.CharField(max_length=254, label="MySQL Database Host", initial='127.0.0.1', required=True)
    mysql_database_port = forms.IntegerField(initial=3306, min_value=1, max_value=65535, label="MySQL Database Port", required=True)
    
    def clean(self):
        super(Phpbb3ServiceAddForm, self).clean()
        test = Phpbb3Service()
        test.mysql_user = self.cleaned_data['mysql_user']
        test.mysql_password = self.cleaned_data['mysql_password']
        test.mysql_database_name = self.cleaned_data['mysql_database_name']
        test.mysql_database_host = self.cleaned_data['mysql_database_host']
        test.mysql_database_port = self.cleaned_data['mysql_database_port']
        if not test.test_connection():
            raise forms.ValidationError("Unable to connect to database.")
        return self.cleaned_data
