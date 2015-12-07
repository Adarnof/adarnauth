from __future__ import unicode_literals

from django.db import models

class EVECharacter(models.Model):
    character_id = models.CharField(max_length=254, primary_key=True)
    character_name = models.CharField(max_length=254)
    corp_id = models.CharField(max_length=254)
    corp_name = models.CharField(max_length=254)
    alliance_id = models.CharField(max_length=254, null=True)
    alliance_name = models.CharField(max_length=254, null=True)
    faction_id = models.CharField(max_length=254, null=True)
    faction_name = models.CharField(max_length=254, null=True)

    def __unicode__(self):
        return self.character_name.encode('utf-8')
