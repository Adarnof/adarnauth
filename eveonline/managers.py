from models import EVECharacter, EVECorporation, EVEAlliance, EVEApiKeyPair
import evelink.api
import evelink.char
import evelink.eve
import evelink.corp
import logging

logger = logging.getLogger(__name__)

class EVEManager:
    @staticmethod
    def get_character_by_id(character_id):
        if not type(character_id) is int:
            try:
                logger.warn("get_character_by_id passed %s, requires int. Converting %s." % (type(character_id), character_id))
                character_id = int(character_id)
            except:
                logger.error("Unable to cast character_id to int. Returning None.")
                return None
        if EVECharacter.objects.filter(id=character_id).exists():
            logger.debug("Returning existing character model with id %s" % character_id)
            return EVECharacter.objects.get(id=character_id)
        else:
            logger.debug("No character model exists for id %s - triggering creation." % character_id)
            chars = EVEManager.create_characters([character_id])
            if chars:
                logger.debug("Returning new character model with id %s" % character_id)
                return chars[0]
            else:
                logger.error("Unable to create character with id %s - returning None" % character_id)
                return None

    @staticmethod
    def create_characters(character_ids):
        chars = []
        for id in character_ids:
            char, created = EVECharacter.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for character id %s" % id)
                if char.update():
                    chars.append(char)
                else:
                    logger.error("Character model population failed for id %s - possible bad id. Deleting." % id)
                    char.delete()
            else:
                logger.warn("Attempting to create existing model for character id %s" % id)
                char.update()
                chars.append(char)
        return chars

    @staticmethod
    def update_characters(character_ids):
        for id in character_ids:
            EVEManager.get_character_by_id(id).update()

    @staticmethod
    def assign_character_user(character, user):
        if character.user:
            logger.warn("Reassigning character from user %s to %s" % (character.user, user))
        character.user = user
        character.save(update_fields=['user'])
        logger.info("Assigned character %s to user %s" % (character, user))

    @staticmethod
    def get_corp_by_id(corp_id):
        if not type(corp_id) is int:
            try:
                logger.warn("get_corp_by_id passed %s, requires int. Converting %s." % (type(corp_id), corp_id))
                corp = int(corp_id)
            except:
                logger.error("Unable to cast corp_id to int. Returning None.")
                return None
        if EVECorporation.objects.filter(id=corp_id).exists():
            logger.debug("Returning existing corp model with id %s" % corp_id)
            return EVECorporation.objects.get(id=corp_id)
        else:
            logger.debug("No corp model exists for id %s - triggering creation." % corp_id)
            corps = EVEManager.create_corps([corp_id])
            if corps:
                logger.debug("Returning new corp model with id %s" % corp_id)
                return corps[0]
            else:
                logger.error("Unable to create corp with id %s - returning None" % corp_id)
                return None            

    @staticmethod
    def create_corps(corp_ids):
        corps = []
        for id in corp_ids:
            corp, created = EVECorporation.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for corp id %s" % id)
                if corp.update():
                    corps.append(corp)
                else:
                    logger.error("Corp model population failed for id %s - possible bad id. Deleting." % id)
                    corp.delete()                    
            else:
                logger.warn("Attempting to create existing model for corp id %s" % id)
                corp.update()
                corps.append(corp)
        return corps

    @staticmethod
    def update_corps(corp_ids):
        for id in corp_ids:
            EVEManager.get_corp_by_id(id).update()

    @staticmethod
    def get_alliance_by_id(alliance_id):
        if not type(alliance_id) is int:
            try:
                logger.warn("get_alliance_by_id passed %s, requires int. Converting %s." % (type(alliance_id), alliance_id))
                alliance_id = int(alliance_id)
            except:
                logger.error("Unable to cast alliance_id to int. Returning None.")
                return None
        if EVEAlliance.objects.filter(id=alliance_id).exists():
            logger.debug("Returning existing alliance model with id %s" % alliance_id)
            return EVEAlliance.objects.get(id=alliance_id)
        else:
            logger.debug("No alliance model exists for id %s - triggering creation." % alliance_id)
            EVEManager.create_alliances([alliance_id])
            logger.debug("Returning new alliance model with id %s" % alliance_id)
            return EVEAlliance.objects.get(id=alliance_id)

    @staticmethod
    def create_alliances(alliance_ids):
        for id in alliance_ids:
            alliance, created = EVEAlliance.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for alliance id %s" % id)
            else:
                logger.warn("Attempting to create existing model for alliance id %s" % id)
            EVEManager.update_alliances([id])

    @staticmethod
    def update_alliances(ids):
        api = evelink.eve.EVE()
        result = api.alliances().result
        for id in ids:
            alliance = EVEManager.get_alliance_by_id(id)
            if id in result:
                logger.debug("Alliance id %s found in alliance list, updating." % id)
                alliance.name = result[id]['name']
                alliance.ticker = result[id]['ticker']
                alliance.save()
                logger.info("Updated alliance info for %s" % alliance)
            else:
                logger.info("Alliance %s no longer exists. Deleting model." % id)
                alliance.delete()
        logger.debug("Finished updating alliance models %s" % ids)

    @staticmethod
    def check_if_character_id_valid(id):
        logger.debug("Checking if %s %s is valid character id" % (type(id), id))
        id = int(id)
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(id).result[id]
        if 'name' in result:
            logger.debug("Determined character id %s is valid" % id)
            return True
        else:
            logger.debug("Determined character id %s is invalid" % id)
            return False

    @staticmethod
    def check_if_corp_id_valid(id):
        logger.debug("Checking if %s %s is valid corp id" % (type(id), id))
        id = int(id)
        a = evelink.api.API()
        api = evelink.corp.Corp(a)
        try:
            result = api.corporation_sheet(corp_id=id).result
            logger.debug("Determined corp id %s is valid" % id)
            return True
        except:
            logger.debug("Determined corp id %s is invalid" % id)
            return False

    @staticmethod
    def check_if_alliance_id_valid(id):
        logger.debug("Checking if %s %s is valid alliance id" % (type(id), id))
        id = int(id)
        api = evelink.eve.EVE()
        result = api.alliances().result
        if id in result:
            logger.debug("Determind alliance id %s is valid" % id)
            return True
        else:
            logger.debug("Determined alliance id %s is invalid" % id)
            return False
        
class EVEApiManager:
    @staticmethod
    def get_characters_from_api(id, vcode):
        chars = []
        logger.debug("Getting characters from api id %s" % id)
        try:
            api = evelink.api.API(api_key=(id, vcode))
            account = evelink.account.Account(api=api)
            chars = account.characters()
        except evelink.api.APIError as error:
            logger.exception("APIError occured while retrieving characters for api id %s" % api_id, exc_info=True)

        logger.debug("Retrieved characters %s from api id %s" % (chars, id))
        return chars

    @staticmethod
    def check_api_is_type_account(id, vcode):
        logger.debug("Checking if api id %s is account." % id)
        try:
            api = evelink.api.API(api_key=(id, vcode))
            account = evelink.account.Account(api=api)
            info = account.key_info()
            logger.debug("API id %s is type %s" % (id, info[0]['type']))
            return info[0]['type'] == "account"

        except evelink.api.APIError as error:
            logger.exception("APIError occured while checking if api id %s is type account" % id, exc_info=True)

        return None

    @staticmethod
    def check_api_key_is_valid(id, vcode):
        logger.debug("Checking if api id %s is valid." % id)
        try:
            api = evelink.api.API(api_key=(id, vcode))
            account = evelink.account.Account(api=api)
            info = account.key_info()
            logger.info("Verified api id %s is valid." % id)
            return True
        except:
            logger.info("API id %s is invalid." % id)
            return False

    @staticmethod
    def check_if_api_server_online():
        logger.debug("Checking if API server online.")
        try:
            api = evelink.api.API()
            server = evelink.server.Server(api=api)
            info = server.server_status()
            logger.info("Verified API server is online and reachable.")
            return True
        except evelink.api.APIError as error:
            logger.exception("APIError occured while trying to query api server status.", exc_info=True)

        logger.warn("Unable to reach API server.")
        return False

    @staticmethod
    def get_corp_standings_from_api(id, vcode):
        try:
            logger.debug("Getting corp standings with api id %s" % id)
            api = evelink.api.API(api_key=(id, vcode))
            corp = evelink.corp.Corp(api=api)
            corpinfo = corp.contacts()
            results = corpinfo[0]
            return results
        except evelink.api.APIError as error:
            logger.exception("APIError occured while retrieving corp standings from api id %s" % id, exc_info=True)
        return {}
