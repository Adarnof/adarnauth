from django.contrib import admin
from models import User
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from eveonline.models import EVECharacter
from django.contrib.auth.admin import UserAdmin

#class UserCreationForm(forms.ModelForm):
#    email  = forms.EmailField(label="Email")
#    main_character = forms.ModelChoiceField(queryset=EVECharacter.objects.all())
#
#    class Meta:
#        model = User
#        fields = ('email', 'main_character')

#    def save(self, commit=True):
 #       user = super(UserCreationForm, self).save(commit=False)
  #      user.set_unusable_password()
   #     if commit:
    #        user.save()
     #   return user

#class UserChangeForm(forms.ModelForm):
 #   class Meta:
  #      model = User
   #     fields = ('email', 'password', 'main_character', 'eve_characters', 'is_active', 'is_staff')

    #password = ReadOnlyPasswordHashField()

#class MyUserAdmin(UserAdmin):
 #   form = UserChangeForm
  #  add_form = UserCreationForm

#    list_display = ('email', 'main_character', 'eve_characters', 'is_staff')
 #   list_filter = ('is_staff',)
  #  fieldsets = (
   #     (None, {'fields': ('email', 'password')}),
    #    ('EVE Associations', {'fields': ('main_character', 'eve_characters')}),
     #   ('Permissions', {'fields': ('is_admin',)}),
#    )


 #   add_fieldsets = (
  #      (None, {
   #         'classes': ('wide',),
    #        'fields': ('email', 'main_character')
     #       }
      #  ),
#    )
 #   search_fields = ('main_character',)
  #  ordering = ('main_character',)
   # filter_horizontal = ()

#admin.site.register(User, MyUserAdmin)
admin.site.register(User)
