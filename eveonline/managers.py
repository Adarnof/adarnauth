from models import EVECharacter
from models import EVECorporation
from models import EVEAlliance
import evelink.api
import evelink.char
import evelink.eve
import evelink.corp
import logging

logger = logging.getLogger(__name__)

class EVEManager:
    @staticmethod
    def get_character_by_id(character_id):
        if EVECharacter.objects.filter(id=character_id).exists():
            logger.debug("Returning existing character model with id %s" % str(character_id))
            return EVECharacter.objects.get(id=character_id)
        else:
            logger.debug("No character model exists for id %s - triggering creation." % str(character_id))
            EVEManager.create_characters([character_id])
            logger.debug("Returning new character model with id %s" % str(character_id))
            return EVECharacter.objects.get(id=character_id)

    @staticmethod
    def create_characters(character_ids):
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(character_ids).result
        logger.debug("Retrieved affiliations for character ids: %s" % str(character_ids))
        for id in character_ids:
            char, created = EVECharacter.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for character id %s" % str(id))
            else:
                logger.warn("Attempting to create existing model for character id %s" % str(id))
        EVEManager.update_characters(result)

    @staticmethod
    def update_characters(result):
        for id in result:
            EVEManager.update_character(id)

    @staticmethod
    def update_character(character_id):
        logger.debug("Initiating character update for id %s" % str(character_id))
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(character_id).result
        logger.debug("Retrieved affiliations for character id %s" % str(character_id))
        char = EVEManager.get_character_by_id(character_id)
        logger.debug("Retrieved character model with id %s" % str(character_id))
        char.name = result[character_id]['name']
        char.corp_id = result[character_id]['corp']['id']
        char.corp_name = result[character_id]['corp']['name']
        if 'faction' in result[character_id]:
            char.faction_id = result[character_id]['faction']['id']
            char.faction_name = result[character_id]['faction']['name']
        else:
            logger.debug("No faction data found for character id %s. Blanking" % str(character_id))
            char.faction_id = None
            char.faction_name = None
        if 'alliance' in result[character_id]:
            char.alliance_id = result[character_id]['alliance']['id']
            char.alliance_name = result[character_id]['alliance']['name']
        else:
            logger.debug("No alliance data found for character id %s. Blanking." % str(character_id))
            char.alliance_id = None
            char.alliance_name = None
        logger.info("Finished updating character id %s from api." % str(character_id))
        char.save()

    @staticmethod
    def assign_character_user(character_id, user):
        character = EVEManager.get_character_by_id(character_id)
        character.user = user
        character.save()
        logger.info("Assigned character id %s to user %s" % (str(character_id), str(user)))

    @staticmethod
    def get_corp_by_id(corp_id):
        if EVECorporation.objects.filter(id=corp_id).exists():
            logger.debug("Returning existing corp model with id %s" % str(corp_id))
            return EVECorporation.objects.get(id=corp_id)
        else:
            logger.debug("No corp model exists for id %s - triggering creation." % str(corp_id))
            EVEManager.create_corps([corp_id])
            logger.debug("Returning new corp model with id %s" % str(corp_id))
            return EVECorporation.objects.get(id=corp_id)

    @staticmethod
    def create_corps(corp_ids):
        for id in corp_ids:
            corp, created = EVECorporation.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for corp id %s" % str(id))
            else:
                logger.warn("Attempting to create existing model for corp id %s" % str(id))
            EVEManager.update_corp(id)

    @staticmethod
    def update_corp(corp_id):
        logger.debug("Updating corp info for corp id %s" % str(corp_id))
        a = evelink.api.API()
        api = evelink.corp.Corp(a)
        result = api.corporation_sheet(corp_id=corp_id).result
        logger.debug("Got corporation sheet from api for corp id %s: name %s ticker %s members %s" % (result['id'], result['name'], result['ticker'], result['members']['current']))
        corp = EVEManager.get_corp_by_id(corp_id)
        logger.debug("Got corp models for id %s" % str(corp_id))
        corp.name = result['name']
        corp.alliance_id = result['alliance']['id']
        corp.alliance_name = result['alliance']['name']
        corp.members = result['members']['current']
        corp.ticker = result['ticker']
        corp.save()
        logger.info("Updated corp info for %s" % str(corp))

    @staticmethod
    def get_alliance_by_id(alliance_id):
        if EVEAlliance.objects.filter(id=alliance_id).exists():
            logger.debug("Returning existing alliance model with id %s" % str(alliance_id))
            return EVEAlliance.objects.get(alliance_id=alliance_id)
        else:
            logger.debug("No alliance model exists for id %s - triggering creation." % str(alliance_id))
            EVEManager.create_alliances([alliance_id])
            logger.debug("Returning new alliance model with id %s" % str(alliance_id))
            return EVEAlliance.objects.get(id=alliance_id)

    @staticmethod
    def create_alliances(alliance_ids):
        for id in alliance_ids:
            alliance, created = EVEAlliance.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for alliance id %s" % str(id))
            else:
                logger.warn("Attempting to create existing model for alliance id %s" % str(id))
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
                logger.info("Updated alliance info for %s" % str(alliance))
            else:
                logger.info("Alliance %s no longer exists. Deleting model." % id)
                alliance.delete()
        logger.debug("Finished updating alliance models %s" % str(ids))
