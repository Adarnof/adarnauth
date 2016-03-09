from celery.task import periodic_task
from celery import shared_task
from celery.task.schedules import crontab
from .models import EVECharacter, EVECorporation, EVEAlliance, EVEContact, EVEApiKeyPair
from authentication.models import User
import evelink
import logging
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

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
def assess_main_char_api_verified(user):
    logger.debug("Checking to see if user %s main character is API verified." % user)
    perm, c = Permission.objects.get_or_create(content_type=ContentType.objects.get_for_model(EVEApiKeyPair), codename='api_verified')
    if user.main_character:
        if user.main_character.apis.filter(is_valid=True).exists():
            logger.debug("User %s main character has valid APIs" % user)
            if not perm in user.user_permissions.all():
                logger.info("User %s main character is API verified. Assigning api_verified permission." % user)
                user.user_permissions.add(perm)
        else:
            logger.debug("User %s main character has no valid APIs" % user)
            if perm in user.user_permissions.all():
                logger.info("User %s main character is not API verified. Removing api_verified permission." % user)
                user.user_permissions.remove(perm)
    else:
        logger.debug("User ID %s missing main character model" % user.main_character_id)
        if perm in user.user_permissions.all():
            logger.warn("User ID %s main character model missing. Unable to determine if API verified. Removing api_verified permission." % user.main_character_id)
            user.user_permissions.remove(perm)
