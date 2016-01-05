from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import ExtendedGroup
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=ExtendedGroup)
def post_save_extendedgroup(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from extendedgroup %s - ensuring owner and admins are members." % instance)
    if not instance.group in instance.owner.groups.all():
        logger.info("User %s is owner of group %s - adding group to user group list." % (instance.owner, instance.group))
        instance.owner.groups.add(instance.group)
    for admin in instance.admins.all():
        if not instance.group in instance.owner.groups.all():
            logger.info("User %s is admin of group %s - adding group to user group list." % (admin, instance.group))
            admin.groups.add(instance.group)

@receiver(post_delete, sender=ExtendedGroup)
def post_delete_extendedgroup(sender, instance, *args, **kwargs):
    logger.info("Received post_delete signal from extendedgroup %s - deleting associated group." % instance)
    instance.group.delete()
