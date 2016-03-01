import logging
from django.dispatch import receiver
from django.db.models.signals import post_delete, post_save, m2m_changed, pre_save
from .models import OpenfireUser, OpenfireGroup, OpenfireService
from access.signals import user_loses_access
from django.contrib.auth.models import Group
from authentication.models import User

logger = logging.getLogger(__name__)

@receiver(m2m_changed, sender=User.groups.through)
def m2m_changed_user_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from user %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        for u in OpenfireUser.objects.filter(user=instance):
            u.service.update_user_groups(u.user)

@receiver(post_delete, sender=OpenfireUser)
def post_delete_openfireuser(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from openfireuser model %s" % instance)
    instance.service._delete_user(instance.username)

@receiver(post_save, sender=OpenfireUser)
def post_save_openfireuser(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from openfireuser model %s" % instance)
    instance.service.update_user_groups(instance.user)

@receiver(m2m_changed, sender=OpenfireUser.openfire_groups.through)
def m2m_changed_openfireuser_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from openfireuser.openfire_groups for %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        group_list=[]
        for g in instance.openfire_groups.all():
            group_list.append(g.group_name)
        instance.service._update_user_groups(instance.username, group_list)

@receiver(post_delete, sender=OpenfireGroup)
def post_delete_openfiregroup(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from openfiregroup %s" % instance)
    for u in instance.openfireuser_set.all():
        u.service._remove_user_from_group(u.username, instance.group_name)

@receiver(post_save, sender=OpenfireGroup)
def post_save_openfiregroup(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from openfiregroup %s" % instance)
    instance.service.sync_groups()

@receiver(post_delete, sender=Group)
def post_delete_group(sender, instance, *args, **kwargs):
    logger.debug("Received post_delete signal from group %s" % instance)
    for g in group.openfiregroup_set.all():
        for u in g.openfireuser_set.all():
            u.service.update_user_groups(u.user)

@receiver(m2m_changed, sender=OpenfireGroup.groups.through)
def m2m_changed_openfiregroup_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from openfiregroup.groups for %s with action %s" % (instance, action))
    if action=="post_add" or action=="post_remove" or action=="post_clear":
        for u in instance.openfireuser_set.all():
            u.service.update_user_groups(u.user)

@receiver(pre_save, sender=OpenfireService)
def pre_save_openfireservice(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from openfireservice %s - testing access" % instance)
    if instance.test_connection() is False:
        raise ValueError("Connecting using new parameters failed.")

@receiver(m2m_changed, sender=OpenfireService.required_groups.through)
def m2m_changed_openfireservice_required_groups(sender, instance, action, *args, **kwargs):
    logger.debug("Received m2m_changed signal from openfireservice.required_groups for service %s with action" % (instance, action))
    if action=="post_add" or action=="post_remove":
        for u in service.openfireuser_set.all():
            if instance.check_user_has_access(u.user) is False:
                u.delete()

@receiver(user_loses_access)
def openfire_user_loses_access(user, *args, **kwargs):
    logger.debug("Received user_loses_access signal from %s" % user)
    for u in user.openfireuser_set.all():
        u.delete()
