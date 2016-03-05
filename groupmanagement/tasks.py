import logging

logger = logging.getLogger(__name__)

def assign_user_auto_group(user, ag):
    logger.debug("Checking to assign %s to %s" % (ag, user))
    if ag.access_rule.access.filter(user=user).exists():
        if not ag.group in user.groups.all():
            logger.info("Adding user %s to %s by %s" % (user, ag.group, ag.access_rule))
            user.groups.add(ag.group)
    else:
        if ag.group in user.groups.all():
            logger.info("Removing user %s from %s" % (user, ag.group))
            user.groups.remove(ag.group)

def assign_auto_group(ag):
    logger.debug("Assigning %s" % ag)
    for a in ag.access_rule.access.all():
        assign_user_auto_group(a.user, ag)
    for u in ag.group.user_set.all():
        assign_user_auto_group(u, ag)
