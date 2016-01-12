from __future__ import unicode_literals

from django.db import models
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from authentication.models import User

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
        if not self.character or not self.user or not self.access_rule:
            logger.info("Deleting incomplete Useraccess %s" % self)
            self.delete()
        elif self.content_type == ContentType.objects.get_for_model(CharacterAccessRule):
            if self.access_rule.character != self.character:
                logger.info("Useraccess %s character does not match characteraccess rule. Deleting" % self)
                self.delete()
        elif self.content_type == ContentType.objects.get_for_model(CorpAccessRule):
            if self.access_rule.corp.id != self.character.corp_id:
                logger.info("Useraccess %s character corp does not match corpaccess rule. Deleting" % self)
                self.delete()
        elif self.content_type == ContentType.objects.get_for_model(AllianceAccessRule):
            if self.access_rule.alliance.id != self.character.alliance_id:
                logger.info("Useraccess %s character alliance does not match allianceaccess rule. Deleting" % self)
                self.delete()
        else:
            logger.info("Useraccess %s based on incorrect type %s - deleting" % (self, self.content_type))
            self.delete()

class CorpAccessRule(models.Model):
    corp = models.OneToOneField(EVECorporation, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'corp %s' % self.corp
        return output.encode('utf-8')

class AllianceAccessRule(models.Model):
    alliance = models.OneToOneField(EVEAlliance, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'alliance %s' % self.alliance
        return output.encode('utf-8')

class CharacterAccessRule(models.Model):
    character = models.OneToOneField(EVECharacter, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'character %s' % self.character
        return output.encode('utf-8')

class StandingAccessRule(models.Model):
    standing = models.OneToOneField(EVEStanding, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'standing %s' % self.standing
        return output.encode('utf-8')
