from __future__ import unicode_literals

from django.db import models
from django.utils.http import urlquote
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from managers import UserManager
from eveonline.models import EVECharacter
import logging

logger = logging.getLogger(__name__)

# Custom user model. Created based on EVE Character supplemented with an email address.
class User(AbstractBaseUser, PermissionsMixin):
    main_character_id = models.CharField(primary_key=True, max_length=254)
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'main_character_id'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def get_short_name(self):
        return self.main_character_id

    def __unicode__(self):
        if self.evecharacter_set.all().filter(id=self.main_character_id).exists():
            return self.evecharacter_set.all().get(id=self.main_character_id).name.encode('utf-8')
        else:
            logger.error("Missing character model for user with main character id %s, returning id as __unicode__." % str(self.main_character_id))
            return self.get_short_name().encode('utf-8')

    def get_characters(self):
        return self.evecharacter_set.all()
