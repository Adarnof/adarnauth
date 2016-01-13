from __future__ import unicode_literals

from django.db import models
import logging
import evelink
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

logger = logging.getLogger(__name__)

class EVECharacter(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=254, blank=True)
    corp_id = models.PositiveIntegerField(null=True, blank=True)
    corp_name = models.CharField(max_length=254, null=True, blank=True)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    faction_id = models.PositiveIntegerField(null=True, blank=True)
    faction_name = models.CharField(max_length=254, null=True, blank=True)
    user = models.ForeignKey('authentication.User', null=True, on_delete=models.SET_NULL, blank=True, related_name='characters')
    standing = GenericRelation('eveonline.EVEStanding', null=True)
    def __unicode__(self):
        if self.name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Character name missing in character model for id %s - needs an update - returning id as __unicode__" % self.id)
            return str(self.id).encode('utf-8')
    def update(self, char_info=None):
        logger.debug("Initiating update for character model with id %s" % str(self.id))
        if not char_info:
            logger.debug("Not passed API result. Grabbing from evelink")
            api = evelink.eve.EVE()
            result = api.affiliations_for_characters(self.id).result
            if not self.id in result:
                logger.error("API result does not contain this character id %s. Aborting update." % self.id)
                return False
            else:
                char_info = result[self.id]
        logger.debug("Retrieved affiliations for character id %s: %s" % (self.id, char_info))
        if (not 'name' in char_info) or (not 'id' in char_info) or (not 'corp' in char_info):
            logger.error("Passed char_info missing required fields for character id %s. Aborting update." % self.id)
            return False
        if not char_info['name']:
            logger.error("Received empty response from evelink for character id %s - likely bad character id. Aborting update." % self.id)
            return False
        if self.id != char_info['id']:
            logger.error("Received api result for different character id %s, refusing to update character id %s" % (char_info['id'], self.id))
            return False
        update_fields = []
        if self.name != char_info['name']:
            self.name = char_info['name']
            update_fields.append('name')
        if self.corp_id != char_info['corp']['id']:
            self.corp_id = char_info['corp']['id']
            update_fields.append('corp_id')
        if self.corp_name != char_info['corp']['name']:
            self.corp_name = char_info['corp']['name']
            update_fields.append('corp_name')
        if 'faction' in char_info:
            if self.faction_id != char_info['faction']['id']:
                self.faction_id = char_info['faction']['id']
                update_fields.append('faction_id')
            if self.faction_name != char_info['faction']['name']:
                self.faction_name = char_info['faction']['name']
                update_fields.append('faction_name')
        else:
            logger.debug("No faction data found for character id %s. Blanking" % self.id)
            if self.faction_id:
                self.faction_id = None
                update_fields.append('faction_id')
            if self.faction_name:
                self.faction_name = None
                update_fields.append('faction_name')
        if 'alliance' in char_info:
            if self.alliance_id != char_info['alliance']['id']:
                self.alliance_id = char_info['alliance']['id']
                update_fields.append('alliance_id')
            if self.alliance_name != char_info['alliance']['name']:
                self.alliance_name = char_info['alliance']['name']
                update_fields.append('alliance_name')
        else:
            logger.debug("No alliance data found for character id %s. Blanking." % self.id)
            if self.alliance_id:
                self.alliance_id = None
                update_fields.append('alliance_id')
            if self.alliance_name:
                self.alliance_name = None
                update_fields.append('alliance_name')
        logger.info("Finished updating character id %s from api. Changed: %s" % (self.id, update_fields))
        if update_fields:
            self.save(update_fields=update_fields)
        return True

class EVECorporation(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    members = models.PositiveIntegerField(null=True, blank=True)
    ticker = models.CharField(max_length=254, null=True, blank=True)
    standing = GenericRelation('eveonline.EVEStanding', null=True)
    def __unicode__(self):
        if self.name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Corp name missing in corp model for id %s - needs an update - returning id as __unicode__" % self.id)
            return str(self.id).encode('utf-8')
    def update(self, result=None):
        logger.debug("Updating corp info for corp id %s" % self.id)
        if not result:
            a = evelink.api.API()
            api = evelink.corp.Corp(a)
            try:
                result = api.corporation_sheet(corp_id=self.id).result
            except:
                logger.exception("Error occured retrieving corporation sheet for id %s - likely bad corp id. Aborting update." % self.id, exc_info=True)
                return False
        if (not 'name' in result) or (not 'alliance' in result) or (not 'members' in result) or (not 'ticker' in result):
            logger.error("Passed corp result missing required fields for corp id %s. Aborting update." % self.id)
            return False
        if self.id != result['id']:
            logger.error("Received api result for different corp id %s, refusing to update corp id %s" % (result['id'], self.id))
            return False
        update_fields = []
        logger.debug("Got corporation sheet from api for corp id %s: name %s ticker %s members %s" % (result['id'], result['name'], result['ticker'], result['members']['current']))
        if self.name != result['name']:
            self.name = result['name']
            update_fields.append('name')
        if self.alliance_id != result['alliance']['id']:
            self.alliance_id = result['alliance']['id']
            update_fields.append('alliance_id')
        if self.alliance_name != result['alliance']['name']:
            self.alliance_name = result['alliance']['name']
            update_fields.append('alliance_name')
        if self.members != result['members']['current']:
            self.members = result['members']['current']
            update_fields.append('members')
        if self.ticker != result['ticker']:
            self.ticker = result['ticker']
            update_fields.append('ticker')
        logger.info("Finished updating corp info for id %s from api. Changed: %s" % (self.id, update_fields))
        if update_fields:
            self.save(update_fields=update_fields)
        return True

class EVEAlliance(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    ticker = models.CharField(max_length=254, null=True, blank=True)
    standing = GenericRelation('eveonline.EVEStanding', null=True)
    def __unicode__(self):
        if self.name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Alliance name missing in alliance models for id %s - needs an update - returning id as __unicode__" % self.id)
            return str(self.id).encode('utf-8')
    def update(self, alliance_info=None):
        logger.debug("Updating alliance info for alliance id %s" % self.id)
        if not alliance_info:
            logger.debug("Not passed API result. Grabbing from evelink")
            api = evelink.eve.EVE()
            result = api.alliances().result
            if self.id in result:
                alliance_info = result[self.id]
            else:
                logger.error("API result does not contain this alliance id %s. Aborting update." % self.id)
                return False
        update_fields=[]
        if self.name != alliance_info['name']:
            self.name = alliance_info['name']
            update_fields.append('name')
        if self.ticker != alliance_info['ticker']:
            self.ticker = alliance_info['ticker']
            update_fields.append('name')
        logger.info("Finished updating alliance info for id %s from api. Changed: %s" % (self.id, update_fields))
        if update_fields:
            self.save(update_fields=update_fields)
        return True

class EVEApiKeyPair(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    vcode = models.CharField(max_length=254)
    owner = models.ForeignKey('authentication.User', null=True)
    is_valid = models.NullBooleanField(blank=True)
    characters = models.ManyToManyField(EVECharacter, related_name ='apis')
    def __unicode__(self):
        return 'API Key %s' % self.id
    def update(self):
        chars = []
        logger.debug("Initiating update of %s" % self)
        try:
            api = evelink.api.API(api_key=(self.id, self.vcode))
            account = evelink.account.Account(api=api)
            api_chars = account.characters().result
            for char in self.characters.all():
                if not char.id in api_chars:
                    logger.info("Character %s no longer found on %s" % (char, self))
                    self.characters.remove(char)
            for api_char_id in api_chars:
                char, c = EVECharacter.objects.get_or_create(id=api_char_id)
                char.update(api_chars[api_char_id])
                if not char in self.characters.all():
                    logger.info("Character %s discovered on %s" % (char, self))
                    self.characters.add(char)
            if not self.is_valid:
                self.is_valid=True
                self.save(update_fields=['is_valid'])
        except evelink.api.APIError as error:
            logger.exception("APIError occured while retrieving characters for %s" % self, exc_info=True)
            logger.info("%s is invalid." % self)
            if self.is_valid or self.is_valid==None:
                self.is_valid=False
                self.save(update_fields=['is_valid'])
            if self.characters.all().exists():
                self.characters.clear()
        

class EVEStanding(models.Model):
    standing = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey('content_type', 'object_id')
    source_api = models.ForeignKey(EVEApiKeyPair, on_delete=models.CASCADE)
    def __unicode__(self):
        output = "%s standing towards %s" % (self.standing, self.content_object)
        return output.encode('utf-8')
    def assign_object(self, object):
        if isinstance(object, EVECharacter) or isinstance(object, EVECorporation) or isinstance(object, EVEAlliance):
            self.object_id = object.pk
            self.content_object = object
        else:
            raise TypeError("Standing must be towards object of type EVECharacter, EVECorporation, EVEAlliance.")
