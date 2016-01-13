from celery.task import periodic_task
from celery import shared_task
from celery.task.schedules import crontab
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, m2m_changed
from .models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding, EVEApiKeyPair
from authentication.models import User
import evelink
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_character_with_result(id, char_info):
    logger.debug("Updating character id %s with info %s" % (id, char_info))
    char = EVECharacter.objects.get(id=id)
    char.update(char_info=char_info)

@shared_task
def update_corp(id):
    logger.debug("Updating corp id %s" % id)
    corp = EVECorporation.objects.get(id=id)
    corp.update()

@shared_task
def update_alliance_with_result(id, alliance_info):
    logger.debug("Updating alliance id with info %s" % (id, alliance_info))
    alliance = EVEAlliance.objects.get(id=id)
    alliance.update(alliance_info=alliance_info)

#@periodic_task(run_every=crontab(minute=0, hour="*/3"))
@shared_task
def update_all_character_models():
    logger.debug("update_all_character_models running")
    chars = EVECharacter.objects.all()
    char_ids = []
    for char in chars:
        char_ids.append(char.id)
    logger.debug("Getting character affiliations for %s characters." % len(char_ids))
    api = evelink.eve.EVE()
    result = api.affiliations_for_characters(char_ids).result
    for id in result:
        update_character_with_result.delay(id, result[id])
    logger.debug("update_all_character_models finished queueing updates")

#@periodic_task(run_every=crontab(minute=0, hour="*/3"))
@shared_task
def update_all_corp_models():
    logger.debug("update_all_corp_models running")
    corps = EVECorporation.objects.all()
    for corp in corps:
        update_corp(corp.id)
    logger.debug("update_all_corp_models finished queueing updates")

#@periodic_task(run_every=crontab(minute=0, hour="*/3"))
@shared_task
def update_all_alliance_models():
    alliances = EVEAlliance.objects.all()
    alliance_ids = []
    for alliance in alliances:
        alliance_ids.append(alliance.id)
    logger.debug("Getting alliance info for %s alliances." % len(alliance_ids))
    api = evelink.eve.EVE()
    result = api.alliances().result
    for id in alliance_ids:
        if id in result:
            update_alliance_with_result.delay(id, result[id])
        else:
            logger.warn("Failed to queue update for alliance %s - not found in active alliance list from API")

@shared_task
def update_api_key(api):
    api.update()

@shared_task
def assess_character_owner(character):
    logger.debug("Assigning new owner for character %s" % character)
    if User.objects.filter(main_character_id=character.id).exists():
        logger.debug("Character %s is a main" % character)
        user = User.objects.get(main_character_id=character.id)
        if character.user != user:
            logger.info("Assigning user %s their main character model %s" % (user, character))
            character.user = user
            character.save(update_fields=['user'])
    else:
        logger.debug("Character %s is not a main. Judging ownership by API keys." % character)
        if character.apis.filter(is_valid=True).exists():
            if character.user:
                if character.apis.filter(is_valid=True).filter(owner=character.user).exists():
                    if character.apis.filter(is_valid=True).exclude(owner=character.user).exists():
                        logger.warn("Character %s has contested ownership via APIs %s" % (character, character.apis.filter(is_valid=True)))
                        character.user = None
                        character.save(update_fields=['user'])
                    else:
                        logger.debug("User %s retain character %s via valid apis %s" % (character.user, character, character.apis.filter(owner=character.user).filter(is_valid=True)))
                else:
                    logger.debug("Current owner %s has no valid apis for character %s" % (character.user, character))
                    if character.apis.filter(is_valid=True).exclude(owner=character.user).exists():
                        logger.debug("Other users have valid APIs for character %s" % character)
                        apis = character.apis.filter(is_valid=True).exclude(owner=character.user)
                        first_api = apis[0]
                        if apis.exclude(owner=first_api.owner).exists():
                            logger.warn("Character %s has contested ownership via APIs %s" % (character, apis))
                            character.user = None
                            character.save(update_fields=['user'])
                        else:
                            logger.info("Assigning ownership of character %s to user %s via %s" % (character, first_api.owner, first_api))
                            character.user = first_api.owner
                            character.save(update_fields=['user'])
                    else:
                        logger.debug("No valid APIs for character %s - removing user %s as owner" % (character, character.user))
                        character.user = None
                        character.save(update_fields=['user'])
            else:
                logger.debug("Users have valid apis for user-less character %s" % character)
                apis = character.apis.filter(is_valid=True)
                first_api = apis[0]
                if apis.exclude(owner=first_api.owner).exists():
                    logger.warn("Character %s has contested ownership - refusing to assign owner - APIs %s" % (character, apis))
                else:
                    logger.info("Assigning ownership of character %s to user %s via %s" % (character, first_api.owner, first_api))
                    character.user = first_api.owner
                    character.save(update_fields=['user'])
        else:
            logger.info("Character %s has no verifiable owner. Clearing model user field." % character)
            if character.user:
                character.user = None
                character.save(update_fields=['user'])

@receiver(post_delete, sender=EVEApiKeyPair)
def post_delete_eveapikeypair(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from eveapikeypair %s" % instance)
    chars = instance.characters.all()
    for char in chars:
        logger.debug("Validating character %s still owned via api" % char)
        for api in char.apis.all():
            if api.owner == char.user:
                logger.debug("Character %s still owned by %s through %s" % (char, char.user, api))
                break
        else:
            if User.objects.filter(main_character_id==char.id).exists():
                logger.debug("Preserving character %s user as is a main." % char)
            else:
                logger.info("Character %s no longer has verified user." % char)
                char.user = None
                char.save(update_fields=['user'])

@receiver(post_save, sender=EVEApiKeyPair)
def post_save_eveapikeypair(sender, instance, update_fields=[], *args, **kwargs):
    if update_fields:
        if 'is_valid' not in update_fields:
           logger.debug("Received post_save signal from %s" % instance)
           update_api_key.delay(instance)

@receiver(m2m_changed, sender=EVEApiKeyPair.characters.through)
def m2m_changed_eveapikeypair_characters(sender, instance, action, model, reverse, pk_set, *args, **kwargs):
    logger.debug("Received m2m_changed signal from %s characters with action %s" % (instance, action))
    if action=="post_remove" or action=="post_add" or action=="post_clear" or action=="post_add":
        chars = []
        if pk_set:
            for pk in pk_set:
                chars.append(model.objects.get(pk=pk))
            logger.debug("%s characters changed in %s" % (len(chars), instance))
            for char in chars:
                assess_character_owner.delay(char)

@receiver(post_delete, sender=User)
def post_delete_user(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from user %s" % instance)
    for char in user.characters.all():
        assess_character_owner.delay(char)
