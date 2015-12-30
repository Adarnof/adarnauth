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
            EVEManager.create_characters([character_id])
            logger.debug("Returning new character model with id %s" % character_id)
            return EVECharacter.objects.get(id=character_id)

    @staticmethod
    def create_characters(character_ids):
        for id in character_ids:
            char, created = EVECharacter.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for character id %s" % id)
            else:
                logger.warn("Attempting to create existing model for character id %s" % id)
            char.update()

    @staticmethod
    def update_characters(character_ids):
        for id in character_ids:
            EVEManager.get_character_by_id(id).update()

    @staticmethod
    def assign_character_user(character_id, user):
        character = EVEManager.get_character_by_id(character_id)
        if character.user:
            logger.warn("Reassigning character from user %s to %s" % (char.user, user))
        character.user = user
        character.save(update_fields=['user'])
        logger.info("Assigned character id %s to user %s" % (character_id, user))

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
            EVEManager.create_corps([corp_id])
            logger.debug("Returning new corp model with id %s" % corp_id)
            return EVECorporation.objects.get(id=corp_id)

    @staticmethod
    def create_corps(corp_ids):
        for id in corp_ids:
            corp, created = EVECorporation.objects.get_or_create(id = id)
            if created:
                logger.info("Created model for corp id %s" % id)
            else:
                logger.warn("Attempting to create existing model for corp id %s" % id)
            corp.update()

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
            return EVEAlliance.objects.get(alliance_id=alliance_id)
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
