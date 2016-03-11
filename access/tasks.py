from __future__ import absolute_import

from celery import shared_task
import logging
from django.contrib.contenttypes.models import ContentType
from access.models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule, StandingAccessRule, ContactAccess
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from eveonline.signals import character_changed_corp, character_changed_alliance, character_changed_user, character_blind_save
from .signals import user_loses_access, user_gains_access
from authentication.models import User
from authentication.signals import user_created

logger = logging.getLogger(__name__)

@shared_task
def assess_access(user):
    logger.debug("Assess access rights for user %s" % user)
    perm, c = Permission.objects.get_or_create(content_type=ContentType.objects.get_for_model(UserAccess), codename='site_access')
    if user.useraccess_set.all().exists():
        logger.debug("User %s gets access because existing access rules %s" % (user, user.useraccess_set.all()))
        if not perm in user.user_permissions.all():
            logger.info("Assigning access permission to user %s: %s" % (user, perm))
            user.user_permissions.add(perm)
            user_gains_access.send(sender=UserAccess, user=user)
    else:
        logger.debug("User %s does not get access because no existing access rules." % user)
        if perm in user.user_permissions.all():
            logger.info("Removing access permission from user %s: %s" % (user, perm))
            user.user_permissions.remove(perm)
            user_loses_access.send(sender=UserAccess, user=user)

@shared_task
def assign_access(user):
    logger.debug("Assigning access for user %s" % user)
    chars = user.characters.all()
    for char in chars:
        logger.debug("Assigning acces for user %s based on character %s" % (user, char))
        if CharacterAccessRule.objects.filter(character=char).exists():
            ca = CharacterAccessRule.objects.get(character=char)
            logger.debug("CharacterAccess rule exists for character %s. Assigning." % char)
            ca.generate_useraccess()
        if EVECorporation.objects.filter(id=char.corp_id).exists():
            logger.debug("Corp model exists for character %s corp %s" % (char, char.corp_name))
            corp = EVECorporation.objects.get(id=char.corp_id)
            if CorpAccessRule.objects.filter(corp=corp).exists():
                ca = CorpAccessRule.objects.get(corp=corp)
                if not ca.access.filter(user=user).filter(character=char).exists():
                    logger.info("CorpAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (ca, user, char))
                    ua = UserAccess(user=user, character=char)
                    ua.set_rule(ca)
                    ua.save()
        if EVEAlliance.objects.filter(id=char.alliance_id).exists():
            logger.debug("Alliance model exists for character %s alliance %s" % (char, char.alliance_name))
            alliance = EVEAlliance.objects.get(id=char.alliance_id)
            if AllianceAccessRule.objects.filter(alliance=alliance).exists():
                aa = AllianceAccessRule.objects.get(alliance=alliance)
                if not aa.access.filter(user=user).filter(character=char).exists():
                    logger.info("AllianceAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (aa, user, char))
                    ua = UserAccess(user=user, character=char)
                    ua.set_rule(aa)
                    ua.save()
    logger.debug("Finished generating useraccess models for user %s" % user)

@receiver(post_delete, sender=UserAccess)
def post_delete_useraccess(sender, instance, *args, **kwargs):
    if instance.user:
        logger.debug("Received post_delete signal from UserAccess models %s. Triggering assessment of user %s access rights." % (instance, instance.user))
        assess_access(instance.user)
    else:
        logger.debug("Received post_delete signal from UserAccess model %s. No affiliated user found. Ignoring." % instance)

@receiver(character_changed_corp, sender=EVECharacter)
def useraccess_check_on_character_changed_corp(sender, character, *args, **kwargs):
    ct = ContentType.objects.get_for_model(CorpAccessRule)
    ua = UserAccess.objects.filter(content_type=ct).filter(character=character)
    logger.debug("Received character_changed_corp signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.access_rule.corp.id != character.corp_id:
            logger.info("Character %s new corp does not apply to corpaccess rule %s - deleting useraccess." % (character, u.access_rule))
            u.delete()
    if character.user:
        logger.debug("Assigning new access rights to character %s owner %s" % (character, character.user))
        assign_access(character.user)
    else:
        logger.debug("Character %s does not have a user. Not assiging access." % character)

@receiver(character_changed_alliance, sender=EVECharacter)
def useraccess_check_on_character_changed_alliance(sender, character, *args, **kwargs):
    ct = ContentType.objects.get_for_model(AllianceAccessRule)
    ua = UserAccess.objects.filter(content_type=ct).filter(character=character)
    logger.debug("Received character_changed_alliance signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.acces_rule.alliance.id != character.alliance_id:
            logger.info("Character %s new alliance does not apply to allianceaccess rule %s - deleting useraccess." % (character, u.access_rule))
    if character.user:
        logger.debug("Assigning new access rights to character %s owner %s" % (character, character.user))
        assign_access(character.user)
    else:
        logger.debug("Character %s does not have a user. Not assiging access." % character)

@receiver(character_changed_user, sender=EVECharacter)
def useraccess_check_on_character_changed_user(sender, character, *args, **kwargs):
    ua = UserAccess.objects.filter(character=character)
    logger.debug("Received character_changed_user signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.user != character.user:
            logger.info("Character %s new user does not match useraccess %s - deleting." % (character, u))
            u.delete()
    if character.user:
        logger.debug("Assigning new access rights to character %s owner %s" % (character, character.user))
        assign_access(character.user)
    else:
        logger.debug("Character %s does not have a user. Not assiging access." % character)


@receiver(character_blind_save, sender=EVECharacter)
def useraccess_check_on_character_blind_save(sender, character, *args, **kwargs):
    logger.debug("Received character_blind_save signal from character %s - checking all useraccess." % character)
    ua = UserAccess.objects.filter(character=character)
    if character.user:
        for u in ua:
            if u.content_type == ContentType.objects.get_for_model(CharacterAccessRule):
                logger.debug("Useraccess %s applied based on characteraccess - verifying still applies to character.")
                if u.access_rule.character != character:
                    logger.info("Useraccess %s character does not match characteraccess rule. Deleting" % u)
                    u.delete()
            elif u.content_type == ContentType.objects.get_for_model(CorpAccessRule):
                logger.debug("Useraccess %s applied based on corpaccess - verifying still applies to character.")
                if u.access_rule.corp.id != character.corp_id:
                    logger.info("Useraccess %s character corp does not match corpaccess rule. Deleting" % u)
                    u.delete()
            elif u.content_type == ContentType.objects.get_for_model(AllianceAccessRule):
                logger.debug("Useraccess %s applied based on allianceaccess - verifying still applies to character.")
                if u.access_rule.alliance.id != character.alliance_id:
                    logger.info("Useraccess %s character alliance does not match allianceaccess rule. Deleting" % u)
                    u.delete()
            elif u.content_type == ContentType.objects.get_for_model(ContactAccess):
                logger.debug("Useraccess %s applied based on standingaccess - verifying still applies to character.")
                if not u.access_rule.check_if_applies_to_character(u.character):
                    logger.info("Useraccess %s character does not match contactaccess rule. Deleting" % u)
                    u.delete()
            else:
                logger.warn("Useraccess %s has no applied rule. Deleting." % u)
                u.delete()
        logger.debug("Assigning new access rights to character %s owner %s" % (character, character.user))
        assign_access(character.user)
    else:
        logger.debug("Character %s no longer has owning user. Deleting all related useraccess." % character)
        for u in ua:
            logger.info("Character %s no longer assigned a user. Deleting useraccess %s" % (character, u))
            u.delete()

@receiver(post_save, sender=UserAccess)
def post_save_useraccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from useraccess %s" % instance)
    if instance.user != instance.character.user:
        logger.info("Useraccess %s character does not match useraccess user. Deleting" % instance)
        instance.delete()
    elif instance.content_type == ContentType.objects.get_for_model(CharacterAccessRule):
        logger.debug("Useraccess based on characteraccess - verifying still applies to character.")
        if instance.character != instance.access_rule.character:
            logger.info("Useraccess %s character does not match characteraccess rule. Deleting" % instance)
            instance.delete()
    elif instance.content_type == ContentType.objects.get_for_model(CorpAccessRule):
        logger.debug("Useraccess based on corpaccess - verifying still applies to character.")
        if instance.access_rule.corp.id != instance.character.corp_id:
            logger.info("Useraccess %s character does not match corpaccess rule. Deleting" % instance)
            instance.delete()
    elif instance.content_type == ContentType.objects.get_for_model(AllianceAccessRule):
        logger.debug("Useraccess based on allianceaccess - verifying still applies to chracter.")
        if instance.access_rule.alliance.id != instance.character.alliance_id:
            logger.info("Useraccess %s character does not match allianceaccess rule. Deleting" % instance)
            instance.delete()
    assess_access(instance.user)

@receiver(post_save, sender=CharacterAccessRule)
def post_save_characteraccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from characteraccess %s" % instance)
    instance.generate_useraccess()

@receiver(post_save, sender=CorpAccessRule)
def post_save_corpaccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from corpaccess %s" % instance)
    instance.generate_useraccess()

@receiver(post_save, sender=AllianceAccessRule)
def post_save_allianceaccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from allianceaccess %s" % instance)
    instance.generate_useraccess()

@receiver(user_created)
def post_user_created(sender, user, *args, **kwargs):
    logger.debug("Received user_created signal from user %s" % user)
    assign_access(user)

@receiver(post_save, sender=StandingAccessRule)
def post_save_standingaccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from standingaccess %s" % instance)
    instance.generate_useraccess()
    instance.generate_contactaccess()

@receiver(post_save, sender=ContactAccess)
def post_save_contactaccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from contactaccess %s" % instance)
    instance.generate_useraccess()
