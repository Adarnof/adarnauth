import logging
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_save
from .models import MumbleUser, MumbleGroup, MumbleService
from access.signals import user_loses_access
from django.contrib.auth.models import Group
from authentication.models import User

logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=User.groups.through)
def m2m_changed_user_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from user.groups for %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        for u in MumbleUser.objects.filter(user=instance):
            u.service.update_user_groups(u.user)

@receiver(post_save, sender=MumbleUser)
def post_save_mumbleuser(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from mumbleuser model %s" % instance)
    instance.service.update_user_groups(instance.user)

@receiver(post_delete, sender=Group)
def post_delete_group(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from group %s" % instance)
    for g in instance.mumblegroup_set.all():
        for u in g.mumbleuser_set.all():
            u.service.update_user_groups(u.user)

@receiver(m2m_changed, sender=MumbleGroup.groups.through)
def m2m_changed_mumblegroup_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from mumblegroup.groups for %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        for u in instance.service.mumbleuser_set.all():
            logger.debug("Triggering update of %s groups" % u)
            instance.service.update_user_groups(u.user)

@receiver(m2m_changed, sender=MumbleService.required_groups.through)
def m2m_changed_mumbleservice_required_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from mumbleservice.required_groups for service %s with action" % (instance, action))
    if action=="post_add" or action=="post_remove":
        for u in service.mumbleuser_set.all():
            if instance.check_user_has_access(u.user) is False:
                u.delete()

@receiver(user_loses_access)
def mumble_user_loses_access(user, *args, **kwargs):
    logger.debug("Received user_loses_access signal from %s" % user)
    for u in user.mumbleuser_set.all():
        u.delete()
