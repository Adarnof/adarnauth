from django import forms

class ServicePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput, max_length=254, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, max_length=254, label="Password Again")

    def clean_password2(self):
        if self.cleaned_data['password'] == self.cleaned_data['password2']:
            return self.cleaned_data['password2']
        raise forms.ValidationError("Passwords do not match")
