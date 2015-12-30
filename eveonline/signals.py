from django.dispatch import receiver, Signal
from django.db.models.signals import post_save
from models import EVECharacter
import logging

logger = logging.getLogger(__name__)

character_changed_name = Signal(providing_args=['character'])
character_changed_corp = Signal(providing_args=['character'])
character_changed_alliance = Signal(providing_args=['character'])
character_changed_faction = Signal(providing_args=['character'])
character_changed_user = Signal(providing_args=['character'])
character_blind_save = Signal(providing_args=['character'])

@receiver(post_save, sender=EVECharacter)
def post_save_evecharacter_dispatcher(sender, instance, update_fields=None, *args, **kwargs):
    logger.debug("Received post_save signal from EVECharacter %s - assessing changes." % instance)
    if not update_fields:
        logger.debug("EVECharacter %s saved without update_fields argument. Sending character_blind_save signal." % instance)
        character_blind_save.send(sender=sender, character=instance)
    else:
        if 'name' in update_fields:
            logger.debug("EVECharacter %s has changed names. Sending character_changed_name signal." % instance)
            character_changed_name.send(sender=sender, character=instance)
        if 'corp_id' in update_fields:
            logger.debug("EVECharacter %s has changed corps. Sending character_changed_corp signal." % instance)
            character_changed_corp.send(sender=sender, character=instance)
        if 'alliance_id' in update_fields:
            logger.debug("EVECharacter %s has changed alliances. Sending character_changed_alliance signal." % instance)
            character_changed_alliance.send(sender=sender, character=instance)
        if 'faction_id' in update_fields:
            logger.debug("EVECharacter %s has changed factions. Sending character_changed_faction signal." % instance)
            character_changed_faction.send(sender=sender, character=instance)
        if 'user' in update_fields:
            logger.debug("EVECharacter %s has changed users. Sending character_changed_user signal." % instance)
            character_changed_user.send(sender=sender, character=instance)
