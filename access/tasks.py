from __future__ import absolute_import

from celery import shared_task
import logging
from django.contrib.contenttypes.models import ContentType
from access.models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Permission
from eveonline.signals import character_changed_corp, character_changed_alliance, character_changed_user

logger = logging.getLogger(__name__)

@shared_task
def assess_access(user):
    logger.debug("Assess access rights for user %s" % user)
    perm = Permission.objects.get(content_type=ContentType.objects.get_for_model(UserAccess), codename='site_access')
    if user.useraccess_set.all().exists():
        logger.debug("User %s gets access because existing access rules %s" % (user, user.useraccess_set.all()))
        if not perm in user.user_permissions.all():
            logger.info("Assigning access permission to user %s: %s" % (user, perm))
            user.user_permissions.add(perm)
            user.save(update_fields="user_permissions")
    else:
        logger.debug("User %s does not get access because no existing access rules." % user)
        if perm in user.user_permissions.all():
            logger.info("Removing access permission from user %s: %s" % (user, permission))
            user.user_permissions.remove(perm)
            user.save(update_fields="user_permissions")

@shared_task
def assign_access(user):
    logger.debug("Assigning access for user %s" % user)
    chars = user.get_characters()
    for char in chars:
        logger.debug("Assigning acces for user %s based on character %s" % (user, char))
        if CharacterAccesRule.objects.filter(character=char).exists():
            ca = CharacterAccessRule.objects.get(character=char)
            logger.debug("CharacterAccess rule exists for character %s. Assigning." % char)
            generate_useraccess_by_characteraccess(ca)
        if EVECorporation.objects.filter(id=char.corp_id).exists():
            logger.debug("Corp model exists for character %s corp %s" % (char, char.corp_name))
            corp = EVECorporation.objects.get(id=char.corp_id)
            if CorpAccessRule.objects.filter(corp=corp).exists():
                ca = CorpAccesRule.objects.get(corp=corp)
                logger.debug("CorpAccess rule exists for corp %s. Assigning." % corp)
                ua = UserAccess(user=user)
                ua.set_rule(ca)
                ua.save()
        if EVEAlliance.objects.filter(id=char.alliance_id).exists():
            logger.debug("Alliance model exists for character %s alliance %s" % (char, char.alliance_name))
            alliance = EVEAlliance.objects.get(id=char.alliance_id)
            if AllianceAccessRule.objects.filter(alliance=alliance).exists():
                aa = AllianceAccessRule.objects.get(alliance=alliance)
                logger.debug("AllianceAccess rule exists for alliance %s. Assigning." % alliance)
                ua = UserAccess(user=user)
                ua.set_rule(aa)
                ua.save()
    logger.info("Finished assigning access to user %s" % user)
    assess_access(user)

@shared_task
def generate_useraccess_by_characteraccess(ca):
    ct = ContentType.objects.get_for_model(ca)
    logger.debug("Assigning UserAccess by CharacterAccess rule %s" % ca)
    char = ca.character
    if char.user:
        user = char.user
        logger.debug("Character for CharacterAccess rule %s has user %s assigned." % (ca, user))
        useraccess = user.useraccess_set.all().filter(content_type = ct)
        for ua in useraccess:
            if ua.access_rule == ca and ua.object_id == ca.id:
                logger.debug("User %s already has CharacterAccess rule %s applied." % (user, ca))
                break
        else:
            logger.debug("User %s does not have CharacterAccess rule %s applied." % (user, ca))
            ua = UserAccess(user=user)
            ua.set_rule(ca)
            ua.save()
    else:
        logger.warn("No user set for character %s. Unable to apply CharacterAccess %s" % (char, ca))

@shared_task
def genereate_useraccess_by_corpaccess(ca):
    ct = ContentType.objects.get_for_model(ca)
    logger.debug("Assigning UserAccess by CorpAccess rule %s" % ca)
    users = User.objects.all()
    for user in users:
        logger.debug("Checking CorpAccess rules for user %s" % user)
        useraccess = user.useraccess_set.all().filter(content_type = ct)
        for ua in useraccess:
            if ua.access_rule == ca and ua.object_id == ca.id:
                logger.debug("User %s already has CorpAccess rule %s applied." % (user, ca))
                break
        else:
            corp = ca.corp
            chars = user.get_characters()
            logger.debug("User %s does not have CorpAccess rule %s applied." % (user, ca))
            for char in chars:
                logger.debug("Checking user's character %s to apply CorpAccess rule %s" % (char, ca))
                if char.corp_id == corp.id:
                    logger.debug("CorpAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (ca, user, char))
                    ua = UserAccess(user = user)
                    ua.set_rule(ca)
                    ua.save()
                    logger.info("Applied CorpAccess rule %s to user %s." % (ca, user))
                    break
            else:
                logger.debug("CorpAccess rule %s does not apply to user %s" % (ca, user))
                continue
    logger.info("Completed assigning CorpAccess rule %s to users." % ca)

@shared_task
def generate_useraccess_by_allianceaccess(aa):
    ct = ContentType.objects.get_for_model(aa)
    logger.debug("Assigning UserAccess by AllianceAccess rule %s" % aa)
    users = User.objects.all()
    for user in users:
        logger.debug("Checking AllianceAccess rules for user %s" % user)
        useraccess = user.useraccess_set.all().filter(content_type = ct)
        for ua in useraccess:
            if ua.access_rule == aa and ua.object_id == aa.id:
                logger.debug("User %s already has AllianceAccess rule %s applied." % (user, aa))
                break
        else:
            alliance = ca.alliance
            chars = user.get_characters()
            logger.debug("User %s does not have AllianceAccess rule %s applied." % (user, aa))
            for char in chars:
                logger.debug("Checking user's character %s to apply AllianceAccess rule %s" % (char, aa))
                if char.alliance_id == alliance.id:
                    logger.debug("AllianceAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (aa, user, char))
                    ua = UserAccess(user = user)
                    ua.set_rule(aa)
                    ua.save()
                    logger.info("Applied AllianceAccess rule %s to user %s." % (aa, user))
                    break
            else:
                logger.debug("AllianceAccess rule %s does not apply to user %s" % (aa, user))
                continue
    logger.info("Completed assigning AllianceAccess rule %s to users." % aa)

@receiver(post_delete, sender=UserAccess)
def post_delete_useraccess(sender, instance, *args, **kwargs):
    if instance.user:
        logger.debug("Received post_delete signal from UserAccess models %s. Triggering assessment of user %s access rights." % (instance, instance.user))
        assess_access.delay(instance.user)
    else:
        logger.debug("Received post_delete signal from UserAccess model %s. No affiliated user found. Ignoring." % instance)

@receiver(character_changed_corp, sender=EVECharacter)
def useraccess_check_on_character_changed_corp(sender, character, *args, **kwargs):
    ct = ContentType.objects.get_for_model(EVECorporation)
    ua = UserAccess.objects.filter(content_type=ct).filter(character=character)
    logger.debug("Received character_changed_corp signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.access_rule.corp.id != character.corp_id:
            logger.info("Character %s new corp does not apply to corpaccess rule %s - deleting useraccess." % (character, u.access_rule))
            u.delete()

@receiver(character_changed_alliance, sender=EVECharacter)
def useraccess_check_on_character_changed_alliance(sender, character, *args, **kwargs):
    ct = ContentType.objects.get_for_model(EVEAlliance)
    ua = UserAccess.objects.filter(content_type=ct).filter(character=character)
    logger.debug("Received character_changed_alliance signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.acces_rule.alliance.id != character.alliance_id:
            logger.info("Character %s new alliance does not apply to allianceaccess rule %s - deleting useraccess." % (character, u.access_rule))

@receiver(character_changed_user, sender=EVECharacter)
def useraccess_check_on_character_changed_user(sender, character, *args, **kwargs):
    ua = UserAccess.objects.filter(character=character)
    logger.debug("Received character_changed_user signal from character %s - checking %s useraccess models." % (character, len(us)))
    for u in ua:
        if u.user != character.user:
            logger.info("Character %s new user does not match useraccess %s - deleting." % (character, u))
            u.delete()
    logger.debug("Assigning new access rights to character %s new owner %s" % (character, character.user))
    assign_access.delay(character.user)

@receiver(post_save, sender=UserAccess)
def post_save_useraccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from useraccess %s" % instance)
    if instance.user != instance.character.user:
        logger.info("Useraccess %s character does not match useraccess user. Deleting" % instance)
        instance.delete()
    elif instance.content_type == ContentType.objects.get_for_model(CharacterAccessRule):
        logger.debug("Useraccess applied based on characteraccess - verifying still applies to character.")
        if instance.character != instance.access_rule.character:
            logger.info("Useraccess %s character does not match characteraccess rule. Deleting" % instance)
            instance.delete()
    elif instance.content_type == ContentType.objects.get_for_model(CorpAccessRule):
        logger.debug("Useraccess applied based on corpaccess - verifying still applies to character.")
        if instance.acces_rule.corp.id != instance.character.corp_id:
            logger.info("Useraccess %s character does not match corpaccess rule. Deleting" % instance)
            instance.delete()
    elif instance.content_type == ContentType.objects.get_for_model(AllianceAccessRule):
        logger.debug("Useraccess applied based on allianceaccess - verifying still applies to chracter.")
        if instance.access_rule.alliance.id != instance.character.alliance_id:
            logger.info("Useraccess %s character does not match allianceaccess rule. Deleting" % instance)
            instance.delete()
