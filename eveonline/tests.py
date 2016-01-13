from django.test import TestCase
from .models import EVECharacter, EVECorporation, EVEAlliance, EVEApiKeyPair
from .managers import EVEManager
from .tasks import assess_character_owner
from authentication.models import User
import evelink
import logging

logger = logging.getLogger(__name__)

class CharacterTestCase(TestCase):
    good_char_id = 234899860
    good_char_name = 'Adarnof'
    bad_char_id = 534899860

    def setUp(self):
        pass

    def test_create_character_good_id(self):
        logger.debug("-----------------------------------------")
        logger.debug("     test_create_character_good_id")
        logger.debug("-----------------------------------------")
        #test bounds of character id
        char = EVECharacter.objects.create(id=self.good_char_id)
        self.assertEqual(char.id, self.good_char_id)
        #test ability to populate fields
        result = char.update()
        self.assertEqual(result, True)
        self.assertEqual(char.name, self.good_char_name)
        char.delete()

    def test_create_character_good_id_via_manager(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_create_character_good_id_via_manager")
        logger.debug("-----------------------------------------")
        #ensure manager correctly returns updated character
        char = EVEManager.get_character_by_id(self.good_char_id)
        self.assertEqual(char.name, self.good_char_name)
        char.delete()

    def test_create_character_bad_id(self):
        logger.debug("-----------------------------------------")
        logger.debug("     test_create_character_bad_id")
        logger.debug("-----------------------------------------")
        char = EVECharacter.objects.create(id=self.bad_char_id)
        self.assertEqual(char.id, self.bad_char_id)
        result = char.update()
        #ensure character fails to populate fields
        self.assertEqual(result, False)
        self.assertEqual(char.name, u'')
        char.delete()

    def test_create_character_bad_id_via_manager(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_create_character_bad_id_via_manager")
        logger.debug("-----------------------------------------")
        #ensures manager refuses to create character with bad id
        char = EVEManager.get_character_by_id(self.bad_char_id)
        self.assertEqual(char, None)

    def test_update_character_with_good_api_result(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_update_character_with_good_api_result")
        logger.debug("-----------------------------------------")
        #ensure model can update self when provided api result
        api = evelink.eve.EVE()
        char_info = api.affiliations_for_characters(self.good_char_id).result[self.good_char_id]
        char = EVECharacter.objects.create(id=self.good_char_id)
        result = char.update(char_info)
        self.assertEqual(result, True)
        char.delete()

    def test_update_character_with_bad_api_result(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_update_character_with_bad_api_result")
        logger.debug("-----------------------------------------")
        char = EVECharacter.objects.create(id=self.good_char_id)
        #ensures model rejects updating with improper api result
        char_info = {'test':'test'}
        result = char.update(char_info)
        self.assertEqual(result, False)
        char.delete()

    def test_update_character_with_mismatched_api_result(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_update_character_with_mismatched_api_result")
        logger.debug("-----------------------------------------")
        #ensures model rejects updating with api result for different character
        api = evelink.eve.EVE()
        char_info = api.affiliations_for_characters(self.good_char_id+1).result[self.good_char_id+1]
        char = EVECharacter.objects.create(id=self.good_char_id)
        result = char.update(char_info)
        self.assertEqual(result, False)
        char.delete()

class CorpTestCase(TestCase):
    good_corp_id = 98317560
    good_corp_ticker = 'LPOST'
    bad_corp_id = 523229765

    def setUp(self):
        pass

    def test_create_corp_good_id(self):
        logger.debug("-----------------------------------------")
        logger.debug("      test_create_corp_good_id")
        logger.debug("-----------------------------------------")
        #test bounds of corp id
        corp = EVECorporation.objects.create(id=self.good_corp_id)
        self.assertEqual(corp.id, self.good_corp_id)
        #test ability to populate fields
        result = corp.update()
        self.assertEqual(result, True)
        corp.delete()

    def test_create_corp_good_id_via_manager(self):
        logger.debug("-----------------------------------------")
        logger.debug("  test_create_corp_good_id_via_manager")
        logger.debug("-----------------------------------------")
        #ensure manager returns corp model with popualted fields
        corp = EVEManager.get_corp_by_id(self.good_corp_id)
        self.assertEqual(corp.id, self.good_corp_id)
        self.assertEqual(corp.ticker, self.good_corp_ticker)
        corp.delete()

    def test_create_corp_bad_id(self):
        logger.debug("-----------------------------------------")
        logger.debug("        test_create_corp_bad_id")
        logger.debug("-----------------------------------------")
        corp = EVECorporation.objects.create(id=self.bad_corp_id)
        self.assertEqual(corp.id, self.bad_corp_id)
        #ensure corp fails to update
        result = corp.update()
        self.assertEqual(result, False)
        self.assertEqual(corp.ticker, None)
        corp.delete()

    def test_create_corp_bad_id_via_manager(self):
        logger.debug("-----------------------------------------")
        logger.debug("   test_create_corp_bad_id_via_manager")
        logger.debug("-----------------------------------------")
        #ensure manager does not create broken corp model
        corp = EVEManager.get_corp_by_id(self.bad_corp_id)
        self.assertEqual(corp, None)

    def test_update_corp_with_good_api_result(self):
        logger.debug("-----------------------------------------")
        logger.debug(" test_update_corp_with_good_api_result")
        logger.debug("-----------------------------------------")
        #ensure corp updates with good api info
        a = evelink.api.API()
        api = evelink.corp.Corp(a)
        corp_sheet = api.corporation_sheet(corp_id=self.good_corp_id).result
        corp = EVECorporation.objects.create(id=self.good_corp_id)
        result = corp.update(corp_sheet)
        self.assertEqual(result, True)
        corp.delete()

    def test_update_corp_with_bad_api_result(self):
        logger.debug("-----------------------------------------")
        logger.debug("  test_update_corp_with_bad_api_result")
        logger.debug("-----------------------------------------")
        #ensure corp refuses to update with missing info
        corp_sheet = {'test':'test'}
        corp = EVECorporation.objects.create(id=self.good_corp_id)
        result = corp.update(result=corp_sheet)
        self.assertEqual(result, False)
        corp.delete()

    def test_update_corp_with_mismatched_api_result(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_update_corp_with_mismatched_api_result")
        logger.debug("-----------------------------------------")
        #ensure corp refuses to update with api result for different corp
        a = evelink.api.API()
        api = evelink.corp.Corp(a)
        corp_sheet = api.corporation_sheet(corp_id=self.good_corp_id+1).result
        corp = EVECorporation.objects.create(id=self.good_corp_id)
        result = corp.update(corp_sheet)
        self.assertEqual(result, False)
        corp.delete()

class AssessCharacterOwnerTest(TestCase):
    def __init__(self, *args, **kwargs):
        super(AssessCharacterOwnerTest, self).__init__(*args, **kwargs)
        self.char = EVECharacter(id=123456, name="Test Character", corp_id=54321, corp_name="Test Corp")
        self.api = EVEApiKeyPair(id=12345, vcode="test api please ignore")
        self.char.save()
        self.api.save()
    def setUp(self):
        self.api.characters.clear()
        self.char.user = None
        self.api.owner = None
        self.char.save()
        self.api.save()
        User.objects.all().delete()
    def test_assess_character_user_as_main(self):
        user = User(main_character_id=self.char.id)
        user.save()
        logger.debug("-----------------------------------------")
        logger.debug("   test_assess_character_user_as_main")
        logger.debug("-----------------------------------------")
        assess_character_owner(self.char)
        self.assertEqual(self.char.user, user)
    def test_assess_character_user_with_good_api(self):
        logger.debug("-----------------------------------------")
        logger.debug(" test_assess_character_user_with_good_api")
        logger.debug("-----------------------------------------")
        self.api.is_valid=True
        user = User(main_character_id=999999)
        user.save()
        self.api.owner = user
        self.api.save()
        self.api.characters.add(self.char)
        assess_character_owner(self.char)
        self.assertEqual(self.char.user, user)
    def test_assess_character_user_with_bad_api(self):
        logger.debug("-----------------------------------------")
        logger.debug(" test_assess_character_user_with_bad_api")
        logger.debug("-----------------------------------------")
        self.api.is_valid=False
        user = User(main_character_id=999999)
        user.save()
        self.api.owner = user
        self.api.save()
        assess_character_owner(self.char)
        self.assertFalse(self.char.user)
    def test_assess_character_user_with_no_api_or_main(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_assess_character_user_with_no_api_or_main")
        logger.debug("-----------------------------------------")
        assess_character_owner(self.char)
        self.assertFalse(self.char.user)
    def test_assess_character_user_change_as_main(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_assess_character_user_change_as_main")
        logger.debug("-----------------------------------------")
        main_user = User(main_character_id=self.char.id)
        main_user.save()
        other_user = User(main_character_id=9999999)
        other_user.save()
        self.char.user = other_user
        self.char.save()
        assess_character_owner(self.char)
        self.assertEqual(self.char.user, main_user)
    def test_assess_character_user_change_on_bad_api(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_assess_character_user_change_on_bad_api")
        logger.debug("-----------------------------------------")
        good_user = User(main_character_id=8888888)
        good_user.save()
        bad_user = User(main_character_id=9999999)
        bad_user.save()
        self.api.characters.add(self.char)
        self.api.owner = good_user
        self.api.is_valid=True
        bad_api = EVEApiKeyPair(id=99999999, vcode="test api please ignore", owner=bad_user)
        bad_api.is_valid=False
        self.char.user = bad_user
        self.api.save()
        bad_api.save()
        bad_api.characters.add(self.char)
        self.char.save()
        assess_character_owner(self.char)
        self.assertEqual(self.char.user, good_user)
    def test_assess_character_user_change_on_new_api(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_assess_character_user_change_on_new_api")
        logger.debug("-----------------------------------------")
        first_user = User(main_character_id=8888888)
        first_user.save()
        new_user = User(main_character_id=9999999)
        new_user.save()
        self.api.characters.add(self.char)
        self.api.owner = first_user
        self.api.is_valid=True
        self.api.save()
        other_api = EVEApiKeyPair(id=9999999, vcode="test api please ignore", owner=new_user)
        other_api.is_valid=True
        other_api.save()
        other_api.characters.add(self.char)
        self.char.user = first_user
        self.char.save()
        assess_character_owner(self.char)
        self.assertFalse(self.char.user)
    def test_assess_character_user_on_last_api_invalid(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_assess_character_user_on_last_api_invalid")
        logger.debug("-----------------------------------------")
        self.api.is_valid=False
        self.api.characters.add(self.char)
        user = User(main_character_id=99999999)
        user.save()
        self.api.owner = user
        self.char.user = user
        self.api.save()
        self.char.save()
        assess_character_owner(self.char)
        self.assertFalse(self.char.user)
    def test_assess_character_user_on_api_invalid_as_main(self):
        logger.debug("-----------------------------------------")
        logger.debug("test_assess_character_user_on_api_invalid_as_main")
        logger.debug("-----------------------------------------")
        self.api.is_valid=False
        self.api.characters.add(self.char)
        user = User(main_character_id=self.char.id)
        user.save()
        self.api.owner = user
        self.char.user = user
        self.api.save()
        self.char.save()
        assess_character_owner(self.char)
        self.assertEqual(self.char.user, user)
