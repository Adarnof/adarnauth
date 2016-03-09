from django.contrib.auth.models import BaseUserManager
from django import forms
from eveonline.models import EVECharacter
from .signals import user_created
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class UserManager(BaseUserManager):
    def _create_user(self, main_character_id, email=None, is_staff=False, is_superuser=False, password=None, **extra_fields):
        logger.info("Creating user for character id: %s" % str(main_character_id))
        if not main_character_id:
            raise ValueError('Users require a main character')
        if email:
            email = self.normalize_email(email)
            logger.debug("Email supplied for user creation: %s" % email)
        user = self.model(main_character_id=main_character_id, email=email, is_staff=is_staff, is_active=True, is_superuser=is_superuser, **extra_fields)
        if password:
            user.set_password(password)
            logger.debug("Received password for user.")
        else:
            user.set_unusable_password()
            logger.debug("Setting unusable password for user.")
        char = EVECharacter.objects.get_by_id(main_character_id)
        logger.debug("Got character model %s for main character id %s" % (char, main_character_id))
        if not char:
            logger.error("Unable to create user with main character id %s - possibly bad id." % main_character_id)
            return None
        user.save()
        char.assign_user()
        logger.debug("User created succesfully: %s" % str(user))
        user_created.send(sender=UserManager, user=user)
        return user

    def create_user(self, main_character_id, email=None, **extra_fields):
        return self._create_user(main_character_id, email, **extra_fields)

    def create_superuser(self, main_character_id, **extra_fields):
        user = self._create_user(main_character_id=main_character_id, is_staff=True, is_superuser=True, **extra_fields)
        user.is_active=True
        user.save()
        logger.info("Created superuser: %s" % str(user))
        return user
        
