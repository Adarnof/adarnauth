from models import CorpAccess, AllianceAccess, CharacterAccess, StandingAccess, UserAccess
from django.db.models.signals import post_delete
from django.dispatch import receiver
import logging
from django.contrib.auth.models import Permission

logger = logging.getLogger(__name__)

@receiver(post_delete, sender=CharacterAccess)
def post_delete_characteraccess(sender, instance, *args, **kwargs):
    logger.info("Received post_delete signal from CharacterAccess model %s. Deleting all related UserAccess" % instance)
    instance.access.all().delete()

@receiver(post_delete, sender=CorpAccess)
def post_delete_corpaccess(sender, instance, *args, **kwargs):
    logger.info("Received post_delete signal from CorpAccess model %s. Deleting all related UserAccess" % instance)
    instance.access.all().delete()

@receiver(post_delete, sender=AllianceAccess)
def post_delete_allianceaccess(sender, instance, *args, **kwargs):
    logger.info("Received post_delete signal from AllianceAccess model %s. Deleting all related UserAccess" % instance)
    instance.access.all().delete()

@receiver(post_delete, sender=StandingAccess)
def post_delete_standingaccess(sender, instance, *args, **kwargs):
    logger.info("Received post_delete signal from StandingAccess model %s. Deleting all related UserAccess" % instance)
    instance.access.all().delete()

@receiver(post_delete, sender=UserAccess)
def post_delete_useraccess(sender, instance, *args, **kwargs):
    if instance.user:
        logger.info("Received post_delete signal from UserAccess models %s. Triggering generation of new UserAccess for user %s" % (instance, instance.user))
        if instance.user.access_set.all().exists():
            logger.info("User %s retains access due to existing access rules." % user)
        else:
            logger.info("Stripping user %s access due to lack of access rules." % user)
            #strip permission command
    else:
        logger.info("Received post_delete signal from UserAccess model %s. No affiliated user found. Ignoring." % instance)
