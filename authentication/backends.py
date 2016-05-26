from eveonline.models import EVECharacter
import logging
from django.contrib.auth import get_user_model
from authentication.models import User

logger = logging.getLogger(__name__)

class TokenAuthenticationBackend(object):
    def authenticate(self, token=None):
        if not token:
            return None
        try:
            char = EVECharacter.objects.get(id=token.character_id)
            if char.user:
                return char.user
            else:
                user = get_user_model().objects.create_user(main_character_id=token.character_id)
                user.save()
                return user
        except EVECharacter.DoesNotExist:
            user = get_user_model().objects.create_user(main_character_id=token.character_id)
            user.save()
            return user
        except:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

