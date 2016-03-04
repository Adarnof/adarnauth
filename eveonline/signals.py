from django.dispatch import receiver, Signal
import logging
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_delete
from models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding, EVEApiKeyPair
from tasks import assess_character_owner, update_api_key, assess_main_char_api_verified
from authentication.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

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

@receiver(post_save, sender=EVEApiKeyPair)
def post_save_eveapikeypair(sender, instance, update_fields=[], *args, **kwargs):
    logger.debug("Received post_save signal from %s" % instance)
    if update_fields:
        if 'is_valid' in update_fields:
            for char in instance.characters.all():
                assess_main_char_api_verified(char.user)
        else:
           logger.debug("Queueing update for %s" % instance)
           update_api_key(instance)
    else:
        logger.debug("Queueing update for %s" % instance)
        update_api_key(instance)
        for char in instance.characters.all():
            assess_main_char_api_verified(char.user)

@receiver(post_delete, sender=User)
def post_delete_user(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from user %s" % instance)
    for char in instance.characters.all():
        assess_character_owner(char)

@receiver(m2m_changed, sender=EVEApiKeyPair.characters.through)
def m2m_changed_eveapikeypair_characters(sender, instance, action, model, pk_set, *args, **kwargs):
    logger.debug("Received m2m_changed signal from %s with action %s" % (instance, action))
    if action=="post_remove" or action=="post_add":
        if pk_set:
            for pk in pk_set:
                char = model.objects.get(pk=pk)
                assess_character_owner(char)
                assess_main_char_api_verified(char.user)
        else:
            logger.warn("m2m_changed signal with action %s for %s characters does not contain an expected pk_set. Unable to assess character ownership" % (action, instance))
    elif action=="pre_clear":
        instance.characters.remove(instance.characters.all())

@receiver(post_delete, sender=EVECharacter)
def post_delete_evecharacter(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from %s" % instance)
    if instance.user:
        assess_main_char_api_verified(instance.user)
