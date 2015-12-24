from __future__ import unicode_literals

from django.db import models
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

class CorpAccess(models.Model):
    corp = models.OneToOneField(EVECorporation, models.CASCADE)
    def __unicode__(self):
        output = 'Access for corp %s' % self.corp
        return output.encode('utf-8')

class AllianceAccess(models.Model):
    alliance = models.OneToOneField(EVEAlliance, models.CASCADE)
    def __unicode__(self):
        output = 'Access for alliance %s' % self.alliance
        return output.encode('utf-8')

class CharacterAccess(models.Model):
    character = models.OneToOneField(EVECharacter, models.CASCADE)
    def __unicode__(self):
        output = 'Access for character %s' % self.character
        return output.encode('utf-8')

class StandingAccess(models.Model):
    standing = models.OneToOneField(EVEStanding, models.CASCADE)
    def __unicode__(self):
        output = 'Access for %s' % self.standing
        return output.encode('utf-8')

class Access(models.Model):
    access_mode = models.NullBooleanField()
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey('content_type', 'object_id')
    def __unicode__(self):
        output = 'Access for %s' % self.content_object
        return output.encode('utf-8')
