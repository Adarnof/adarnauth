from __future__ import absolute_import

from celery import shared_task
import logging
from django.contrib.contenttypes.models import ContentType
from access.models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule
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
            generate_useraccess_by_characteraccess(ca)
        if EVECorporation.objects.filter(id=char.corp_id).exists():
            logger.debug("Corp model exists for character %s corp %s" % (char, char.corp_name))
            corp = EVECorporation.objects.get(id=char.corp_id)
            if CorpAccessRule.objects.filter(corp=corp).exists():
                ca = CorpAccessRule.objects.get(corp=corp)
                if ca.access.filter(user=user).filter(character=char).exists() is not True:
                    logger.info("CorpAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (ca, user, char))
                    ua = UserAccess(user=user, character=char)
                    ua.set_rule(ca)
                    ua.save()
        if EVEAlliance.objects.filter(id=char.alliance_id).exists():
            logger.debug("Alliance model exists for character %s alliance %s" % (char, char.alliance_name))
            alliance = EVEAlliance.objects.get(id=char.alliance_id)
            if AllianceAccessRule.objects.filter(alliance=alliance).exists():
                aa = AllianceAccessRule.objects.get(alliance=alliance)
                if aa.access.filter(user=user).filter(character=char).exists() is not True:
                    logger.info("AllianceAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (aa, user, char))
                    ua = UserAccess(user=user, character=char)
                    ua.set_rule(aa)
                    ua.save()
    logger.debug("Finished generating useraccess models for user %s" % user)
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
                if ua.character == char:
                    logger.debug("User %s already has CharacterAccess rule %s applied to %s" % (user, ca, char))
                    break
                else:
                    logger.info("Characteraccess %s has changed character. Deleting useraccess %s" % (ca, ua))
                    ua.delete()
                    break
        else:
            logger.info("CorpAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (ca, char.user, char))
            ua = UserAccess(user=user, character=char)
            ua.set_rule(ca)
            ua.save()
    else:
        logger.warn("No user set for character %s. Unable to apply CharacterAccess %s" % (char, ca))

@shared_task
def generate_useraccess_by_corpaccess(ca):
    ct = ContentType.objects.get_for_model(ca)
    logger.debug("Assigning UserAccess by CorpAccess rule %s" % ca)
    users = User.objects.all()
    for user in users:
        logger.debug("Checking CorpAccess rules for user %s" % user)
        useraccess = user.useraccess_set.all().filter(content_type = ct)
        for ua in useraccess:
            if ua.access_rule == ca and ua.object_id == ca.id:
                if ua.character.corp_id == ca.corp.id:
                    logger.debug("User %s already has CorpAccess rule %s applied to %s" % (user, ca, ua.character))
                    break
                else:
                    logger.info("Corpaccess %s has changed corp. Deleting useraccess %s" % (ca, ua))
                    ua.delete()
                    break
        else:
            corp = ca.corp
            chars = user.characters.all()
            logger.debug("User %s does not have CorpAccess rule %s applied." % (user, ca))
            for char in chars:
                logger.debug("Checking user's character %s to apply CorpAccess rule %s" % (char, ca))
                if char.corp_id == corp.id:
                    logger.info("CorpAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (ca, user, char))
                    ua = UserAccess(user=user, character=char)
                    ua.set_rule(ca)
                    ua.save()
                    logger.debug("Applied CorpAccess rule %s to user %s." % (ca, user))
                    break
            else:
                logger.debug("CorpAccess rule %s does not apply to user %s" % (ca, user))
                continue
    logger.debug("Completed assigning CorpAccess rule %s to users." % ca)

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
                if ua.character.alliance_id == aa.alliance.id:
                    logger.debug("User %s already has AllianceAccess rule %s applied." % (user, aa))
                    break
                else:
                    logger.info("Allianceaccess %s has changed alliance. Deleting useraccess %s" % (aa, ua))
                    ua.delete()
                    break
        else:
            alliance = aa.alliance
            chars = user.characters.all()
            logger.debug("User %s does not have AllianceAccess rule %s applied." % (user, aa))
            for char in chars:
                logger.debug("Checking user's character %s to apply AllianceAccess rule %s" % (char, aa))
                if char.alliance_id == alliance.id:
                    logger.info("AllianceAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (aa, user, char))
                    ua = UserAccess(user=user, character=char)
                    ua.set_rule(aa)
                    ua.save()
                    logger.debug("Applied AllianceAccess rule %s to user %s." % (aa, user))
                    break
            else:
                logger.debug("AllianceAccess rule %s does not apply to user %s" % (aa, user))
                continue
    logger.debug("Completed assigning AllianceAccess rule %s to users." % aa)

@receiver(post_delete, sender=UserAccess)
def post_delete_useraccess(sender, instance, *args, **kwargs):
    if instance.user:
        logger.debug("Received post_delete signal from UserAccess models %s. Triggering assessment of user %s access rights." % (instance, instance.user))
        assess_access.delay(instance.user)
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
    logger.debug("Assigning new access rights to character %s owner %s" % (character, character.user))
    assign_access.delay(character.user)

@receiver(character_changed_alliance, sender=EVECharacter)
def useraccess_check_on_character_changed_alliance(sender, character, *args, **kwargs):
    ct = ContentType.objects.get_for_model(AllianceAccessRule)
    ua = UserAccess.objects.filter(content_type=ct).filter(character=character)
    logger.debug("Received character_changed_alliance signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.acces_rule.alliance.id != character.alliance_id:
            logger.info("Character %s new alliance does not apply to allianceaccess rule %s - deleting useraccess." % (character, u.access_rule))
    logger.debug("Assigning new access rights to character %s owner %s" % (character, character.user))
    assign_access.delay(character.user)

@receiver(character_changed_user, sender=EVECharacter)
def useraccess_check_on_character_changed_user(sender, character, *args, **kwargs):
    ua = UserAccess.objects.filter(character=character)
    logger.debug("Received character_changed_user signal from character %s - checking %s useraccess models." % (character, len(ua)))
    for u in ua:
        if u.user != character.user:
            logger.info("Character %s new user does not match useraccess %s - deleting." % (character, u))
            u.delete()
    logger.debug("Assigning new access rights to character %s new owner %s" % (character, character.user))
    assign_access.delay(character.user)

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

@receiver(post_save, sender=CharacterAccessRule)
def post_save_characteraccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from characteraccess %s" % instance)
    generate_useraccess_by_characteraccess.delay(instance)

@receiver(post_save, sender=CorpAccessRule)
def post_save_corpaccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from corpaccess %s" % instance)
    generate_useraccess_by_corpaccess.delay(instance)

@receiver(post_save, sender=AllianceAccessRule)
def post_save_allianceaccess(sender, instance, *args, **kwargs):
    logger.debug("Received post_save signal from allianceaccess %s" % instance)
    generate_useraccess_by_allianceaccess.delay(instance)

@receiver(user_created)
def post_user_created(sender, user, *args, **kwargs):
    logger.debug("Received user_created signal from user %s" % user)
    assign_access(user)
