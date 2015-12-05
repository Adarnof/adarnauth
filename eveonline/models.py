from __future__ import unicode_literals

from django.db import models

class EVECharacter(models.Model):
    character_id = models.CharField(max_length=254, primary_key=True)
    character_name = models.CharField(max_length=254)
    corporation_id = models.CharField(max_length=254)
    corporation_name = models.CharField(max_length=254)
    alliance_id = models.CharField(max_length=254)
    alliance_name = models.CharField(max_length=254)
    faction_id = models.CharField(max_length=254)
    faction_name = models.CharField(max_length=254)

    def __str__(self):
        return self.character_name
