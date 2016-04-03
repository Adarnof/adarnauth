from django.contrib import admin
from django import forms
from models import EVECharacter, EVECorporation, EVEAlliance, EVEApiKeyPair, EVEContact, EVEContactSet

class EVECharacterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EVECharacterForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['corp_id'].widget.attrs['readonly'] = True
        self.fields['corp_name'].widget.attrs['readonly'] = True
        self.fields['alliance_id'].widget.attrs['readonly'] = True
        self.fields['alliance_name'].widget.attrs['readonly'] = True
        self.fields['faction_id'].widget.attrs['readonly'] = True
        self.fields['faction_name'].widget.attrs['readonly'] = True
        self.fields['user'].widget.attrs['disabled'] = True
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True

    def clean_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['id'] != instance.id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.id
        else:
            if EVECharacter.objects.check_id(self.cleaned_data['id']):
                return self.cleaned_data['id']
            else:
                raise forms.ValidationError("Failed to verify via API")
    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return None
    def clean_corp_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.corp_id
        else:
            return None
    def clean_corp_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.corp_name
        else:
            return None
    def clean_alliance_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_id
        else:
            return None
    def clean_alliance_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_name
        else:
            return None
    def clean_faction_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.faction_name
        else:
            return None
    def clean_faction_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.faction_id
        else:
            return None
    def clean_user(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['user'] != instance.user:
                self.data['user'] = instance.user
                raise forms.ValidationError("Automatically determined, cannot be manually set")
            else:
                return instance.user
        elif self.cleaned_data['user']:
            self.data['user'] = None
            raise forms.ValidationError("Automatically determined, cannot be manually set")
        return None

class EVECorporationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EVECorporationForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['alliance_id'].widget.attrs['readonly'] = True
        self.fields['alliance_name'].widget.attrs['readonly'] = True
        self.fields['members'].widget.attrs['readonly'] = True
        self.fields['ticker'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True
    def clean_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['id'] != instance.id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.id
        else:
            if EVECorporation.objects.check_id(self.cleaned_data['id']):
                return self.cleaned_data['id']
            else:
                raise forms.ValidationError("Failed to verify via API")
    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return None
    def clean_alliance_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_id
        else:
            return None
    def clean_alliance_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.alliance_name
        else:
            return None
    def clean_members(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.members
        else:
            return 0
    def clean_ticker(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.ticker
        else:
            return None

class EVEAllianceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EVEAllianceForm, self).__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['readonly'] = True
        self.fields['ticker'].widget.attrs['readonly'] = True
        instance = getattr(self, 'instance', None)
        if instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True
    def clean_id(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['id'] != instance.id:
                raise forms.ValidationError("Cannot change once set")
            else:
                return instance.id
        else:
            if EVEAlliance.objects.check_id(self.cleaned_data['id']):
                return self.cleaned_data['id']
            else:
                raise forms.ValidationError("Failed to verify via API")
    def clean_name(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.name
        else:
            return None
    def clean_ticker(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.ticker
        else:
            return None

class EVEApiKeyPairForm(forms.ModelForm):
    characters_on_key = forms.CharField(widget=forms.Textarea(attrs={'readonly': True}), required=False)

    class Meta:
        exclude = ['characters']

    def __init__(self, *args, **kwargs):
        super(EVEApiKeyPairForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['id'].widget.attrs['readonly'] = True
            self.fields['vcode'].widget.attrs['readonly'] = True
        self.fields['is_valid'].widget.attrs['disabled'] = True
        self.fields['type'].widget.attrs['disabled'] = True
        self.fields['access_mask'].widget.attrs['readonly'] = True
        self.fields['corp'].widget.attrs['disabled'] = True
        if instance and instance.pk:
            chars = ""
            for char in instance.characters.all():
                chars = chars + str(char) + "\n"
            self.fields['characters_on_key'].initial = chars.strip("\n")
    def clean_is_valid(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.is_valid
        else:
            return None
    def clean_access_mask(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.access_mask
        else:
            return 0
    def clean_type(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.type
        else:
            return None
    def clean_is_valid(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.is_valid
        else:
            return None
    def clean_corp(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['corp'] != instance.corp:
                self.data['corp'] = instance.corp
                raise forms.ValidationError("Automatically determined, cannot be manually set")
            else:
                return instance.corp
        elif self.cleaned_data['corp']:
            self.data['corp'] = None
            raise forms.ValidationError("Automatically determined, cannot be manually set")
        return None


class EVEContactForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EVEContactForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['standing'].widget.attrs['readonly'] = True
            self.fields['object_id'].widget.attrs['readonly'] = True
            self.fields['object_name'].widget.attrs['readonly'] = True
    def clean_standing(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.standing
        else:
            return self.cleaned_data['standing']
    def clean_object_id(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.object_id
        else:
            return self.cleaned_data['object_id']
    def clean_object_name(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.object_name
        else:
            return self.cleaned_data['object_name']
    def clean_type(self):
        instance = getattr(self, 'instance', None)
        if instance:
            return instance.type
        else:
            return self.cleaned_data['type']
    def clean_contact_source(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['contact_source'] != instance.contact_source:
                self.data['contact_source'] = instance.contact_source
                raise forms.ValidationError("Cannot change once set")
            return instance.contact_source
        return self.cleaned_data['contact_source']

class EVEContactSetForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(EVEContactSetForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['minimum_standing'].widget.attrs['readonly'] = True
            self.fields['level'].widget.attrs['disabled'] = True

    def clean_minimum_standing(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.minimum_standing
        else:
            return self.cleaned_data['minimum_standing']
    def clean_level(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            return instance.level
        else:
            return self.cleaned_data['level']
    def clean_source_api(self):
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            if self.cleaned_data['source_api'] != instance.source_api:
                self.data['source_api'] = instance.source_api
                raise forms.ValidationError("Cannot change once set")
            return instance.source_api
        return self.cleaned_data['source_api']

@admin.register(EVECharacter)
class EVECharacterAdmin(admin.ModelAdmin):
    form = EVECharacterForm

@admin.register(EVECorporation)
class EVECorporationAdmin(admin.ModelAdmin):
    form = EVECorporationForm

@admin.register(EVEAlliance)
class EVEAllianceAdmin(admin.ModelAdmin):
    form = EVEAllianceForm

@admin.register(EVEApiKeyPair)
class EVEApiKeyPairAdmin(admin.ModelAdmin):
    form = EVEApiKeyPairForm

@admin.register(EVEContact)
class EVEContactAdmin(admin.ModelAdmin):
    form = EVEContactForm

admin.site.register(EVEContactSet)
