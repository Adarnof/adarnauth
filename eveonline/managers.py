from models import EVECharacter
import evelink.api
import evelink.char
import evelink.eve
import logging

logger = logging.getLogger(__name__)

class EVEManager:
    @staticmethod
    def get_character_by_id(character_id):
        if EVECharacter.objects.filter(character_id=character_id).exists():
            logger.debug("Returning existing character model with id %s" % str(character_id))
            return EVECharacter.objects.get(character_id=character_id)
        else:
            logger.debug("No character model exists for id %s - triggering creation." % str(character_id))
            EVEManager.create_characters([character_id])
            logger.debug("Returning new character model with id %s" % str(character_id))
            return EVECharacter.objects.get(character_id=character_id)

    @staticmethod
    def create_characters(character_ids):
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(character_ids).result
        logger.debug("Retrieved affiliations for character ids: %s" % str(character_ids))
        for id in character_ids:
            char, created = EVECharacter.objects.get_or_create(character_id = id)
            if created:
                logger.info("Created model for character id %s" % str(id))
            else:
                logger.warn("Attempting to create existing models for character id %s" % str(id))
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
        char.character_id = character_id
        char.character_name = result[character_id]['name']
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
