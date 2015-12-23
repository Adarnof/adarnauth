from django.contrib.auth.models import BaseUserManager
from django import forms
from eveonline.managers import EVEManager
from datetime import datetime
import requests
from django.conf import settings
import base64

class UserManager(BaseUserManager):
    def _create_user(self, main_character_id, email=None, is_staff=False, is_superuser=False, password=None, **extra_fields):
        if not main_character_id:
            raise ValueError('Users require a main character')
        if email:
            email = self.normalize_email(email)
        user = self.model(main_character_id=main_character_id, email=email, is_staff=is_staff, is_active=False, is_superuser=is_superuser, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        main_character = EVEManager.get_character_by_id(main_character_id)
        user.save()
        main_character.user = user
        main_character.save()
        return user

    def create_user(self, main_character_id, email=None, **extra_fields):
        return self._create_user(main_character_id, email, **extra_fields)

    def create_superuser(self, main_character_id, **extra_fields):
        user = self._create_user(main_character_id=main_character_id, is_staff=True, is_superuser=True, **extra_fields)
        user.is_active=True
        user.save()
        return user

class AuthenticationManager:
    def authenticate(self, code=None):
        #first we need to exchange the code for a token
        client_id = settings.SSO_CLIENT_ID
        client_secret = settings.SSO_CLIENT_SECRET
        authorization_code = ':'.join(client_id, client_secret)
        code_64 = base64.b64encode(authorization_code.encode('utf-8'))
        authorization = 'Basic ' + code_64
        custom_headers = {
            'Authorization': authorization,
            'content-type': 'application/json',
        }
        data = {
            'grant_type': 'authorization_code',
            'code': code,
        }
        path = "https://login.eveonline.com/oauth/token"
        r = requests.post(path, headers=custom_headers, json=data)
        r.raise_for_status()
        token = r.json()['access_token']

        #now pull character ID from token
        custom_headers = {'Authorization': 'Bearer ' + token}
        path = "https://login.eveonline.com/oauth/verify"
        r = requests.get(path, headers=custom_headers)
        r.raise_for_status()
        character_id = r.json()['CharacterID']

        #check if character model exists to return user
        if EVECharacter.objcets.filter(pk=character_id).exists():
            character = EVECharacter.objects.get(pk=character_id)
            if character.user:
                return character.user
        #user does not exist for that character
        user = User.objects.create(character_id)
        return user

    #internet says I need this
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
            
