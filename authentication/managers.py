from django.contrib.auth.models import BaseUserManager
from django import forms
from eveonline.managers import EVEManager
from datetime import datetime

class UserManager(BaseUserManager):
    def _create_user(self, main_character_id, email, is_staff=False, is_superuser=False, password=None, **extra_fields):
        if not main_character_id:
            raise ValueError('Users require a main character')
        if not email:
            raise ValueError('Users require an email address')
        main_character = EVEManager.get_character_by_id(main_character_id)
        email = self.normalize_email(email)
        user = self.model(main_character=main_character, email=email, is_staff=is_staff, is_active=False, is_superuser=is_superuser, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, main_character, email=None, **extra_fields):
        return self._create_user(main_character, email, **extra_fields)

    def create_superuser(self, email, main_character, **extra_fields):
        user = self._create_user(main_character, email, True, True, **extra_fields)
        user.is_active=True
        user.save(using=self._db)
        return user
