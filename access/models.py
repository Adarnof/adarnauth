from __future__ import unicode_literals

from django.db import models
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from authentication.models import User
import logging

logger = logging.getLogger(__name__)

class UserAccess(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    access_rule = GenericForeignKey('content_type', 'object_id')
    character = models.ForeignKey(EVECharacter, on_delete=models.CASCADE)

    def __unicode__(self):
        output = '%s access by rule for %s applying to %s' % (self.user, self.access_rule, self.character)
        return output.encode('utf-8')

    class Meta:
        permissions = (("site_access", "User has access to site."), ("manage_access", "User can manage site access."), ("audit_access", "User can view access granted per rule."))

    def set_rule(self, object):
        if isinstance(object, CharacterAccessRule) or isinstance(object, CorpAccessRule) or isinstance(object, AllianceAccessRule) or isinstance(object, StandingAccessRule):
            self.object_id = object.pk
            self.access_rule = object
        else:
            raise TypeError("Access rule must be of type CharacterAccessRule, CorpAccessRule, AllianceAccessRule, StandingAccessRule")

    def get_rule(self):
        return self.access_rule

    def verify(self):
        self.save()

class CorpAccessRule(models.Model):

    corp = models.OneToOneField(EVECorporation, models.CASCADE)
    access = GenericRelation(UserAccess)
    auto_group = GenericRelation('groupmanagement.AutoGroup')

    def __unicode__(self):
        output = 'corp %s' % self.corp
        return output.encode('utf-8')

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by CorpAccess rule %s" % self)
        characters = EVECharacter.objects.filter(corp_id=self.corp.id)
        useraccess = UserAccess.objects.filter(content_type=ct).filter(object_id=self.id)
        for char in characters:
            if not char.user:
                logger.debug("CorpAccess %s applies to character %s but they have no user." % (self, char))
            elif useraccess.filter(character=char).exists():
                logger.debug("CorpAccess %s already applied to character %s" % (self, char))
            else:
                logger.info("Applying CorpAccess %s to user %s through character %s" % (self, char.user, char))
                ua = UserAccess(user=char.user, character=char)
                ua.set_rule(self)
                ua.save()
        for ua in useraccess:
            if not ua.character in characters:
                logger.info("CorpAccess %s no longer applies to %s because %s is not in corp" % (self, ua.user, ua.character))
                ua.delete()
                continue
            if ua.character.user != ua.user:
                logger.info("CorpAccess %s no longer applies to %s because UserAccess and Character %s users don't match" % (self, ua.user, ua.character))
                ua.delete()
                continue
            logger.debug("UserAccess %s confirmed still valid." % ua)
        logger.debug("Completed assigning CorpAccess rule %s to users." % self)


class AllianceAccessRule(models.Model):

    alliance = models.OneToOneField(EVEAlliance, models.CASCADE)
    access = GenericRelation(UserAccess)
    auto_group = GenericRelation('groupmanagement.AutoGroup')

    def __unicode__(self):
        output = 'alliance %s' % self.alliance
        return output.encode('utf-8')

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by AllianceAccess rule %s" % self)
        characters = EVECharacter.objects.filter(alliance_id=self.alliance.id)
        useraccess = UserAccess.objects.filter(content_type=ct).filter(object_id=self.id)
        for char in characters:
            if not char.user:
                logger.debug("AllianceAccess %s applies to character %s but they have no user." % (self, char))
            elif useraccess.filter(character=char).exists():
                logger.debug("AllianceAccess %s already applied to character %s" % (self, char))
            else:
                logger.info("Applying AllianceAccess %s to user %s through character %s" % (self, char.user, char))
                ua = UserAccess(user=char.user, character=char)
                ua.set_rule(self)
                ua.save()
        for ua in useraccess:
            if not ua.character in characters:
                logger.info("AllianceAccess %s no longer applies to %s because %s is not in alliance" % (self, ua.user, ua.character))
                ua.delete()
                continue
            if ua.character.user != ua.user:
                logger.info("AllianceAccess %s no longer applies to %s because UserAccess and Character %s users don't match" % (self, ua.user, ua.character))
                ua.delete()
                continue
            logger.debug("UserAccess %s confirmed still valid." % ua)
        logger.debug("Completed assigning AllianceAccess rule %s to users." % self)

class CharacterAccessRule(models.Model):

    character = models.OneToOneField(EVECharacter, models.CASCADE)
    access = GenericRelation(UserAccess)
    auto_group = GenericRelation('groupmanagement.AutoGroup')

    def __unicode__(self):
        output = 'character %s' % self.character
        return output.encode('utf-8')

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by CharacterAccess rule %s" % self)
        char = self.character
        useraccess = self.access.filter(content_type=ct).filter(object_id=self.id)
        if char.user:
            user = char.user
            logger.debug("Character for CharacterAccess rule %s has user %s assigned." % (self, user))
            for ua in useraccess:
                if ua.character == char:
                    logger.debug("User %s already has CharacterAccess rule %s applied to %s" % (user, self, char))
                else:
                    logger.info("Characteraccess %s has changed character. Deleting useraccess %s" % (self, ua))
                    ua.delete()
            if not useraccess.filter(user=char.user).exists():
                logger.info("CharacterAccess rule %s applies to user %s by character %s. Assigning UserAccess model." % (self, char.user, char))
                ua = UserAccess(user=user, character=char)
                ua.set_rule(self)
                ua.save()
        else:
            logger.debug("No user set for character %s. Unable to apply CharacterAccess %s" % (char, ca))
            useraccess.all().delete()

class StandingAccessRule(models.Model):

    standing = models.OneToOneField(EVEStanding, models.CASCADE)
    access = GenericRelation(UserAccess)

    def __unicode__(self):
        output = 'standing %s' % self.standing
        return output.encode('utf-8')
