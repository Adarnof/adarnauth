from django.test import TestCase
from .models import User
from .managers import UserManager
import logging

logger = logging.getLogger(__name__)

class UserTestCate(TestCase):
    def setUp(self):
        pass

    def test_create_user_with_good_char_id(self):
        logger.debug("-----------------------------------------")
        logger.debug("   test_create_user_with_good_char_id")
        logger.debug("-----------------------------------------")
        #ensure generating character and assigning user
        main_character_id = 234899860
        user = User.objects.create_user(main_character_id=main_character_id)
        #ensure user has characters
        self.assertEqual(len(user.characters.all()), 1)

    def test_create_user_with_bad_char_id(self):
        logger.debug("-----------------------------------------")
        logger.debug("   test_create_user_with_bad_char_id")
        logger.debug("-----------------------------------------")
        #ensure failing to generate character
        main_character_id = 534899860
        user = User.objects.create_user(main_character_id=main_character_id)
        #ensure user lacks characters
        self.assertEqual(user, None)
