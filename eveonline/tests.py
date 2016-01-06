from django.test import TestCase
from .models import EVECharacter, EVECorporation, EVEAlliance
from .managers import EVEManager
import evelink

# Create your tests here.

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
