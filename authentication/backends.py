from django.conf import settings
import requests
from eveonline.models import EVECharacter
import base64
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class AuthenticationBackend(object):
    def authenticate(self, code=None):
        logger.debug("Attempting login with code: " + code)
        if not code:
            logger.debug("No code supplied, unable to get user model.")
            return None
        #first we need to exchange the code for a token
        client_id = settings.SSO_CLIENT_ID
        client_secret = settings.SSO_CLIENT_SECRET
        authorization_code = '%s:%s' % (client_id, client_secret)
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
        if not r.status_code in [200, 201]:
            logger.error("Received bad status from code exchange: " + r.status_code)
            return None
        token = r.json()['access_token']
        logger.debug("Received access token: " + token)

        #now pull character ID from token
        custom_headers = {'Authorization': 'Bearer ' + token}
        path = "https://login.eveonline.com/oauth/verify"
        r = requests.get(path, headers=custom_headers)
        if not r.status_code in [200,201]:
            logger.error("Received bad status from token validation: " + r.status_code)
            return None
        character_id = r.json()['CharacterID']
        logger.debug("Received character id " + str(character_id))

        #check if character model exists to return user
        if EVECharacter.objects.filter(character_id=character_id).exists():
            character = EVECharacter.objects.get(character_id=character_id)
            logger.debug("EVECharacter model exists for character id " + str(character_id))
            if character.user:
                logger.debug("Retrieved user for character id " + str(character_id))
                return character.user
        #user does not exist for that character
        logger.debug("No user found for character id " + str(character_id))
        user = get_user_model().objects.create_user(main_character_id=character_id)
        user.save()
        logger.debug("Retrieved user for character id " + str(character_id))
        return user

    #internet says I need this
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
