from models import EVECharacter
import evelink.api
import evelink.char
import evelink.eve

class EVEManager:

    @staticmethod
    def get_character_by_id(character_id):
        if EVECharacter.objects.filter(character_id=character_id).exists():
            return EVECharacter.objects.get(character_id=character_id)
        else:
            EVEManager.create_characters([character_id])
            return EVECharacter.objects.get(character_id=character_id)

    @staticmethod
    def create_characters(character_ids):
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(character_ids).result
        for id in character_ids:
            char, created = EVECharacter.objects.get_or_create(character_id = id)
        EVEManager.update_characters(result)

    @staticmethod
    def update_characters(result):
        for id in result:
            EVEManager.update_character(id)

    @staticmethod
    def update_character(character_id):
        api = evelink.eve.EVE()
        result = api.affiliations_for_characters(character_id).result
        char = EVEManager.get_character_by_id(character_id)
        char.character_id = character_id
        char.character_name = result[character_id]['name']
        char.corp_id = result[character_id]['corp']['id']
        char.corp_name = result[character_id]['corp']['name']
        if 'faction' in result[character_id]:
            char.faction_id = result[character_id]['faction']['id']
            char.faction_name = result[character_id]['faction']['name']
        else:
            char.faction_id = None
            char.faction_name = None
        if 'alliance' in result[character_id]:
            char.alliance_id = result[character_id]['alliance']['id']
            char.alliance_name = result[character_id]['alliance']['name']
        else:
            char.alliance_id = None
            char.alliance_name = None
        char.save()
