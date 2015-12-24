from __future__ import unicode_literals

from django.db import models
import logging

logger = logging.getLogger(__name__)

class EVECharacter(models.Model):
    id = models.CharField(max_length=254, primary_key=True)
    name = models.CharField(max_length=254)
    corp_id = models.CharField(max_length=254)
    corp_name = models.CharField(max_length=254)
    alliance_id = models.CharField(max_length=254, null=True)
    alliance_name = models.CharField(max_length=254, null=True)
    faction_id = models.CharField(max_length=254, null=True)
    faction_name = models.CharField(max_length=254, null=True)
    user = models.ForeignKey('authentication.User', null=True)
    def __unicode__(self):
        if self.character_name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Character name missing in character model for id %s - returning id as __unicode__" % self.id)
            return self.id.encode('utf-8')

class EVECorporation(models.Model):
    id = models.CharField(max_length=254, primary_key=True)
    name = models.CharField(max_length=254)
    alliance_id = models.CharField(max_length=254, null=True)
    alliance_name = models.CharField(max_length=254, null=True)
    members = models.CharField(max_length=254)
    ticker = models.CharField(max_length=254)
    def __unicode__(self):
        if self.name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Corp name missing in corp model for id %s - returning id as __unicode__" % self.id)
            return self.id.encode('utf-8')

class EVEAlliance(models.Model):
    id = models.CharField(max_length=254, primary_key=True)
    name = models.CharField(max_length=254)
    ticker = models.CharField(max_length=254)
    def __unicode__(self):
        if self.alliance_name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Alliance name missing in alliance models for id %s - returning id as __unicode__" % self.id)
            return self.id.encode('utf-8')

class EVEApiKeyPair(models.Model):
    id = models.CharField(max_length=254, primary_key=True)
    vcode = models.CharField(max_length=254)
    owner = models.ForeignKey('authentication.User', null=True)
    is_valid = models.NullBooleanField()
    def __unicode__(self):
        return 'API Key %s' % self.id
