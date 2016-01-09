from django.conf import settings
import requests
from eveonline.models import EVECharacter
from .tasks import get_character_id_from_sso_code
import base64
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class AuthenticationBackend(object):
    def authenticate(self, code=None):
        logger.debug("Attempting login with SSO callback code %s" % code)
        if not code:
            logger.debug("No code supplied, unable to get user model.")
            return None
        character_id = get_character_id_from_sso_code(code)
        if character_id is None:
            logger.debug("Failed to retrieve character id from sso")
            return None
        #check if character model exists to return user
        if EVECharacter.objects.filter(id=character_id).exists():
            character = EVECharacter.objects.get(id=character_id)
            logger.debug("EVECharacter model exists for character id %s" % character_id)
            if character.user:
                logger.debug("Retrieved user for character id %s" % character_id)
                return character.user
        #user does not exist for that character
        logger.debug("No user found for character id %s" % character_id)
        user = get_user_model().objects.create_user(main_character_id=character_id)
        user.save()
        logger.debug("Retrieved user for character id %s" % character_id)
        return user

    #internet says I need this
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
