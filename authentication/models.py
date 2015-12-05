from __future__ import unicode_literals

from django.db import models
from django.utils.http import urlquote
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from managers import UserManager

# Custom user model. Created based on EVE Character supplemented with an email address.
class User(AbstractBaseUser, PermissionsMixin):
    main_character = models.ForeignKey('eveonline.EVECharacter', models.PROTECT, primary_key=True)
    email = models.EmailField(max_length=255)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    eve_characters = models.ManyToManyField('eveonline.EVECharacter', related_name='alts')

    USERNAME_FIELD = 'main_character'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def get_short_name(self):
        return self.main_character.character_name
