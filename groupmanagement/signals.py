from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import ExtendedGroup
import logging
from access.signals import user_loses_access
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

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
    logger.debug("Ensuring owner is not listed as admin.")
    if instance.owner in instance.admins.all():
        logger.info("Removing user %s from group %s admins as is owner." % (instance.owner, instance))
        instance.admins.remove(instance.owner)
    

@receiver(post_delete, sender=ExtendedGroup)
def post_delete_extendedgroup(sender, instance, *args, **kwargs):
    logger.info("Received post_delete signal from extendedgroup %s - deleting associated group." % instance)
    instance.group.delete()

@receiver(user_loses_access)
def group_validation_on_user_loses_access(sender, user, *args, **kwargs):
    logger.debug("Received user_loses_access signal from user %s - revoking all groups." % user)
    perm, c = Permission.objects.get_or_create(content_type=ContentType.objects.get_for_model(ExtendedGroup), codename='can_manage_groups')
    for g in user.owned_groups.all():
        logger.debug("Attempting to assign new owner for group %s by checking %s admins" % (g, len(g.admins.all())))
        for a in g.admins.all():
            if perm in a.user_permissions.all():
                logger.info("Changing group %s owner to %s as user %s has lost site access." % (g, a, user))
                g.owner = a
                g.save()
                break
            else:
                logger.debug("Group %s admin %s unsuitable owner replacement because lacks permission %s" % (g, a, perm))
        else:
            logger.info("Group %s owner %s has lost access and no suitable replacements found. Deleting." % (g, user))
            g.delete()
    for g in user.admin_groups.all():
        logger.info("Removing user %s from group %s administrators - user has lost access." % (user, g))
        g.admins.remove(user)
    logger.info("Removing all groups from user %s as user has lost access." % user)
    user.groups.clear()
