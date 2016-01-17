import logging
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_save
from .models import Phpbb3User, Phpbb3Group, Phpbb3Service
from access.signals import user_loses_access
from django.contrib.auth.models import Group
from authentication.models import User

logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=User.groups.through)
def m2m_changed_user_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from user %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        for u in Phpbb3User.objects.filter(user=instance):
            u.service.update_user_groups(u.user)

@receiver(post_delete, sender=Phpbb3User)
def post_delete_phpbb3user(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from phpbb3user model %s" % instance)
    instance.service._delete_user(instance.username)

@receiver(post_save, sender=Phpbb3User)
def post_save_phpbb3user(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from phpbb3user model %s" % instance)
    instance.service.update_user_groups(instance.user)

@receiver(m2m_changed, sender=Phpbb3User.phpbb_groups.through)
def m2m_changed_phpbb3user_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from phpbb3user.phpbb_groups for %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        group_list=[]
        for g in instance.phpbb3_groups.all():
            group_list.append(g.group_id)
        instance.service._update_user_groups(instance.user_id, group_list)

@receiver(post_delete, sender=Phpbb3Group)
def post_delete_phpbb3group(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from phpbb3group %s" % instance)
    for u in instance.phpbb3user_set.all():
        u.service._remove_user_from_group(u.user_id, instance.group_id)

@receiver(post_save, sender=Phpbb3Group)
def post_save_phpbb3group(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from phpbb3group %s" % instance)
    instance.service.sync_groups()

@receiver(post_delete, sender=Group)
def post_delete_group(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from group %s" % instance)
    for g in group.phpbb3group_set.all():
        for u in g.phpbb3user_set.all():
            u.service.update_user_groups(u.user)

@receiver(m2m_changed, sender=Phpbb3Group.groups.through)
def m2m_changed_phpbb3group_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from phpbb3group.groups for %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        for u in instance.phpbb3user_set.all():
            u.service.update_user_groups(u.user)

@receiver(pre_save, sender=Phpbb3Service)
def pre_save_phpbb3service(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from phpbbservice %s - testing access" % instance)
    if instance.test_connection() is False:
        raise ValueError("Connecting using new parameters failed.")

@receiver(m2m_changed, sender=Phpbb3Service.required_groups.through)
def m2m_changed_phpbb3service_required_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from phpbb3service.required_groups for service %s with action" % (instance, action))
    if action=="post_add" or action=="post_remove":
        for u in service.phpbb3user_set.all():
            if instance.check_user_has_access(u.user) is False:
                u.delete()

@receiver(user_loses_access)
def phpbb_user_loses_access(user, *args, **kwargs):
    logger.debug("Received user_loses_access signal from %s" % user)
    for u in user.phpbb3user_set.all():
        u.delete()
