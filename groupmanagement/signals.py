from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver, Signal
from models import ExtendedGroup, GroupApplication, AutoGroup
import logging
from access.signals import user_loses_access
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission
from tasks import assign_auto_group, assign_user_auto_group
from access.models import UserAccess

logger = logging.getLogger(__name__)

user_joins_group = Signal(providing_args=['user', 'group'])
user_leaves_group = Signal(providing_args=['user', 'group'])

@receiver(post_save, sender=GroupApplication)
def post_save_groupapplication(sender, instance, update_fields=None, *args, **kwargs):
    logger.debug("Received post_save signal from groupapplication %s " % instance)
    if update_fields:
        if 'response' in update_fields:
            if instance.response == None:
                pass
            elif instance.response:
                logger.info("%s accepted. Adding user to group." % instance)
                instance.user.groups.add(instance.group)
                user_joins_group.send(sender=GroupApplication, user=instance.user, group=instance.group)

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

@receiver(post_save, sender=AutoGroup)
def post_save_autogroup(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from %s" % instance)
    assign_auto_group(instance)

@receiver(post_delete, sender=AutoGroup)
def post_delete_autogroup(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from %s" % instance)
    logger.info("Cascading %s deletion to base group %s" % (instance, instance.group))
    instance.group.delete()

@receiver(post_save, sender=UserAccess)
def post_save_useraccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from %s" % instance)
    if AutoGroup.objects.filter(content_type=instance.content_type).filter(object_id=instance.object_id).exists():
        for ag in AutoGroup.objects.filter(content_type=instance.content_type).filter(object_id=instance.object_id):
            assign_user_auto_group(instance.user, ag)

@receiver(post_delete, sender=UserAccess)
def post_delete_useraccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from %s" % instance)
    if AutoGroup.objects.filter(content_type=instance.content_type).filter(object_id=instance.object_id).exists():
        for ag in AutoGroup.objects.filter(content_type=instance.content_type).filter(object_id=instance.object_id):
            assign_user_auto_group(instance.user, ag)
