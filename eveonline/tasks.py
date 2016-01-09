from celery.task import periodic_task
from celery import shared_task
from celery.task.schedules import crontab
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save
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
