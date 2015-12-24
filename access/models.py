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
    content_object = GenericForeignKey('content_type', 'object_id')
    def __unicode__(self):
        output = '%s access by rule for %s' % (self.user, self.content_object)
        return output.encode('utf-8')
    class Meta:
        permissions = (("site_access", "User has access to site."),)

class CorpAccess(models.Model):
    corp = models.OneToOneField(EVECorporation, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'corp %s' % self.corp
        return output.encode('utf-8')

class AllianceAccess(models.Model):
    alliance = models.OneToOneField(EVEAlliance, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'alliance %s' % self.alliance
        return output.encode('utf-8')

class CharacterAccess(models.Model):
    character = models.OneToOneField(EVECharacter, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'character %s' % self.character
        return output.encode('utf-8')

class StandingAccess(models.Model):
    standing = models.OneToOneField(EVEStanding, models.CASCADE)
    access = GenericRelation(UserAccess)
    def __unicode__(self):
        output = 'standing %s' % self.standing
        return output.encode('utf-8')
