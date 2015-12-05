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
            char = EVEManager.get_character_by_id(id)
            char.character_id = id
            char.character_name = result[id]['name']
            char.corp_id = result[id]['corp']['id']
            char.corp_name = result[id]['corp']['name']
            if 'faction' in result[id]:
                char.faction_id = result[id]['faction']['id']
                char.faction_name = result[id]['faction']['name']
            else:
                char.faction_id = None
                char.faction_name = None
            if 'alliance' in result[id]:
                char.alliance_id = result[id]['alliance']['id']
                char.alliance_name = result[id]['alliance']['name']
            else:
                char.alliance_id = None
                char.alliance_name = None
            char.save()
