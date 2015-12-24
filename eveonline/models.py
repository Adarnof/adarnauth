from __future__ import unicode_literals

from django.db import models
import logging

logger = logging.getLogger(__name__)

class EVECharacter(models.Model):
    character_id = models.CharField(max_length=254, primary_key=True)
    character_name = models.CharField(max_length=254)
    corp_id = models.CharField(max_length=254)
    corp_name = models.CharField(max_length=254)
    alliance_id = models.CharField(max_length=254, null=True)
    alliance_name = models.CharField(max_length=254, null=True)
    faction_id = models.CharField(max_length=254, null=True)
    faction_name = models.CharField(max_length=254, null=True)
    user = models.ForeignKey('authentication.User', null=True)
    def __unicode__(self):
        if self.character_name:
            return self.character_name.encode('utf-8')
        else:
            logger.warn("Character name missing in character model for id %s - returning id as __unicode__" % self.character_id)
            return self.character_id.encode('utf-8')

class EVECorporation(models.Model):
    corp_id = models.CharField(max_length=254, primary_key=True)
    corp_name = models.CharField(max_length=254)
    alliance_id = models.CharField(max_length=254)
    alliance_name = models.CharField(max_length=254)
    members = models.CharField(max_length=254)
    ticker = models.CharField(max_length=254)
    def __unicode__(self):
        if self.corp_name:
            return self.corp_name.encode('utf-8')
        else:
            logger.warn("Corp name missing in corp model for id %s - returning id as __unicode__" % self.corp_id)
            return self.corp_id.encode('utf-8')
