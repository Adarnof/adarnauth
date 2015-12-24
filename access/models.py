from __future__ import unicode_literals

from django.db import models
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding

class CorpAccess(models.Model):
    corp = models.ForeignKey(EVECorporation, on_delete=models.CASCADE, unique=True)
    def __unicode__(self):
        output = 'Access for corp %s' % self.corp
        return output.encode('utf-8')

class AllianceAccess(models.Model):
    alliance = models.ForeignKey(EVEAlliance, on_delete=models.CASCADE, unique=True)
    def __unicode__(self):
        output = 'Access for alliance %s' % self.alliance
        return output.encode('utf-8')

class CharacterAccess(models.Model):
    character = models.ForeignKey(EVECharacter, on_delete=models.CASCADE, unique=True)
    def __unicode__(self):
        output = 'Access for character %s' % self.character
        return output.encode('utf-8')

class StandingAccess(models.Model):
    standing = models.ForeignKey(EVEStanding, on_delete=models.CASCADE, unique=True)
    def __unicode__(self):
        output = 'Access for %s' % self.standing
        return output.encode('utf-8')
