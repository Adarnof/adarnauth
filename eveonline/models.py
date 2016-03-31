from __future__ import unicode_literals

from django.db import models
import logging
import evelink
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from managers import EVECharacterManager, EVECorporationManager, EVEAllianceManager, EVEContactManager, EVEApiKeyPairManager

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

    objects = EVECharacterManager()

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
        if update_fields:
            logger.info("Finished updating character id %s from api. Changed: %s" % (self.id, update_fields))
            self.save(update_fields=update_fields)
        if self.corp_id == EVECharacterManager.DOOMHEIM_CORP_ID:
            logger.info("%s has been biomassed. Deleting model" % self)
            self.delete()
        return True

    def get_possible_users(self):
        from authentication.models import User
        users = set([])
        if User.objects.filter(main_character_id=self.id).exists():
            logger.debug("A user account exists with main_character_id %s" % self.id)
            users.add(User.objects.get(main_character_id=self.id))
        for api in self.apis.filter(is_valid=True).filter(owner__isnull=False):
            logger.debug("%s containing this character has an owner" % api)
            users.add(api.owner)
        logger.debug("Found %s possible owners for %s" % (len(users), self))
        return list(users)

    def assign_user(self):
        users = self.get_possible_users()
        if len(users) == 1:
            logger.debug("%s is not contested and has one possible user" % self)
            if self.user != users[0]:
                logger.debug("Changing assigned user of %s from %s to %s" % (self, self.user, users[0]))
                self.user = users[0]
                self.save(update_fields=['user'])
            else:
                logger.debug("%s has correct user assigned" % self)
        else:
            if len(users) > 1:
                logger.debug("%s is in a contested state with %s possible users: %s" % (self, len(users), users))
            else:
                logger.debug("No possible users found for %s" % self)
            if self.user:
                self.user = None
                self.save(update_fields=['user'])

class EVECorporation(models.Model):

    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=254, null=True, blank=True)
    alliance_id = models.PositiveIntegerField(null=True, blank=True)
    alliance_name = models.CharField(max_length=254, null=True, blank=True)
    members = models.PositiveIntegerField(null=True, blank=True)
    ticker = models.CharField(max_length=254, null=True, blank=True)

    objects = EVECorporationManager()

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
            except evelink.api.APIError as e:
                if int(e.code) == 523:
                    logger.info("%s has closed. Deleting model" % self)
                    self.delete()
                else:
                    logger.exception("Error occured retrieving corporation sheet for id %s - aborting update." % self.id, exc_info=True)
                    return False
            except:
                logger.exception("Error occured retrieving corporation sheet for id %s - aborting update." % self.id, exc_info=True)
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

    objects = EVEAllianceManager()

    def __unicode__(self):
        if self.name:
            return self.name.encode('utf-8')
        else:
            logger.warn("Alliance name missing in alliance models for id %s - needs an update - returning id as __unicode__" % self.id)
            return str(self.id).encode('utf-8')

    def update(self, alliance_info=None):
        logger.debug("Updating alliance info for alliance id %s" % self.id)
        if not alliance_info:
            logger.debug("Not passed API result. Grabbing from manager")
            alliance_info = EVEAlliance.objects.get_info(self.id)
        if alliance_info['corporationsCount'] == 0:
            logger.info("%s has closed. Deleting model" % self)
            self.delete()
        update_fields=[]
        if self.name != alliance_info['name']:
            self.name = alliance_info['name']
            update_fields.append('name')
        if self.ticker != alliance_info['shortName']:
            self.ticker = alliance_info['shortName']
            update_fields.append('ticker')
        logger.info("Finished updating alliance info for id %s from api. Changed: %s" % (self.id, update_fields))
        if update_fields:
            self.save(update_fields=update_fields)
        return True

class EVEApiKeyPair(models.Model):

    TYPE_CHOICES = (
        ('account', 'account'),
        ('character', 'character'),
        ('corp', 'corp'),
        )

    id = models.PositiveIntegerField(primary_key=True)
    vcode = models.CharField(max_length=254)
    owner = models.ForeignKey('authentication.User', null=True, blank=True)
    is_valid = models.NullBooleanField(blank=True)
    access_mask = models.IntegerField(default=0, blank=True)
    type = models.CharField(max_length=11, choices=TYPE_CHOICES, blank=True)
    characters = models.ManyToManyField(EVECharacter, blank=True, related_name='apis')
    corp = models.ForeignKey(EVECorporation, null=True, blank=True, related_name='apis')

    objects = EVEApiKeyPairManager()

    class Meta:
        permissions = (("api_verified", "Main character has valid API."),)

    def __unicode__(self):
        return 'API Key %s' % self.id

    def validate(self):
        logger.debug("Checking if api id %s is valid." % id)
        try:
            api = evelink.api.API(api_key=(self.id, self.vcode))
            account = evelink.account.Account(api=api)
            info = account.key_info()
            logger.debug("Verified api id %s is valid." % id)
            return True
        except evelink.api.APIError as e:
            if int(e.code) == 403:
                logger.debug("API id %s is invalid." % id)
                return False
            else:
                raise e

    def get_standings(self):
        if self.contacts:
            if self.type == 'corp':
                try:
                    logger.debug("Getting corp standings with api id %s" % id)
                    api = evelink.api.API(api_key=(self.id, self.vcode))
                    corp = evelink.corp.Corp(api=api)
                    corpinfo = corp.contacts().result
                    return corpinfo
                except evelink.api.APIError as error:
                    logger.exception("APIError occured while retrieving corp standings from api id %s" % id, exc_info=True)
                    return {}
            else:
                raise NotImplementedError('Only corp keys are supported')
        else:
            raise AttributeError("%s lacks access mask 16 (ContactList)" % self)

    def update(self):
        chars = []
        logger.debug("Initiating update of %s" % self)
        try:
            api = evelink.api.API(api_key=(self.id, self.vcode))
            account = evelink.account.Account(api=api)
            update_fields = []
            key_info = account.key_info().result
            if key_info['type'] != self.type:
                self.type = key_info['type']
                update_fields.append('type')
            if key_info['access_mask'] != self.access_mask:
                self.access_mask = key_info['access_mask']
                update_fields.append('access_mask')
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
            if self.type == 'corp':
                for id in key_info['characters']:
                    corp_id = key_info['characters'][id]['corp']['id']
                    break
                api_corp = evelink.corp.Corp(api=api).corporation_sheet(corp_id=corp_id).result
                corp = EVECorporation.objects.get_by_id(corp_id)
                if self.corp != corp:
                    self.corp = corp
                    update_fields.append('corp')
            else:
                if self.corp:
                    self.corp = None
                    update_fields.append('corp')
            if not self.is_valid:
                self.is_valid=True
                update_fields.append('is_valid')
            if update_fields:
                logger.info("%s updated %s" % (self, update_fields))
                self.save(update_fields=update_fields)
        except evelink.api.APIError as e:
            if int(e.code) in [500, 520]:
                logger.error("EVE API servers encountered an error. Unable to update %s" % self)
            elif int(e.code) in [221]:
                logger.error("API hiccup prevented updating %s" % self)
            else:
                logger.info("%s is invalid, error code %s" % (self, e.code))
                update_fields = []
                if self.is_valid or self.is_valid==None:
                    self.is_valid=False
                    update_fields.append('is_valid')
                if self.characters.all().exists():
                    for char in self.characters.all():
                        self.characters.remove(char)
                if self.corp:
                    self.corp = None
                    update_fields.append('corp')
                if update_fields:
                    logger.info("%s updated %s" % (self, update_fields))
                    self.save(update_fields=update_fields)

class EVEContactSet(models.Model):
    LEVEL_CHOICES = (
        ('personal', 'character'),
        ('corp', 'corporation'),
        ('alliance', 'alliance'),
    )

    source_api = models.OneToOneField(EVEApiKeyPair, on_delete=models.CASCADE, limit_choices_to=EVEApiKeyPair.objects.get_contact_source_apis)
    minimum_standing = models.IntegerField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)

    def __unicode__(self):
        output = "Standings above %s from %s" % (self.minimum_standing, self.source_api)
        return output.encode('utf-8')

    def update(self):
        logger.debug("Updating %s" % self)
        all_contact_dict = self.source_api.get_standings()
        contact_dict = {}
        if self.level in all_contact_dict:
            contact_dict = all_contact_dict[self.level]
        contacts = self.contacts.all()
        logger.debug("Got %s contacts from API and %s contact models" % (len(contact_dict), len(contacts)))
        for contact in contacts:
            if not contact.object_id in contact_dict:
                logger.info("Contact with %s no longer found on %s" % (contact, self.source_api))
                contact.delete()
            elif contact_dict[contact.object_id]['standing'] < self.minimum_standing:
                logger.info("Contact with %s no longer meets minimum requirements of %s" % (contact, self))
                contact.delete()
            else:
                logger.debug("Contact %s still valid" % contact)
        for id in contact_dict:
            if contact_dict[id]['standing'] >= self.minimum_standing:
                if not contacts.filter(object_id=id).exists():
                    contact = EVEContact.objects.create_from_api(contact_dict[id], self)
                    logger.info("Created contact with %s from %s" % (contact, self))
        logger.debug("Updated contacts from %s" % self)


class EVEContact(models.Model):

    TYPE_CHOICES = (
        ('alliance', 'alliance'),
        ('corp', 'corp'),
        ('character', 'character'),
    )

    standing = models.DecimalField(max_digits=3, decimal_places=1, null=True)
    object_id = models.IntegerField()
    object_name = models.CharField(max_length=254, blank=True, null=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, blank=True, null=True)
    contact_source = models.ForeignKey(EVEContactSet, on_delete=models.CASCADE, related_name='contacts')

    class Meta:
        unique_together = ('object_id', 'contact_source')

    def __unicode__(self):
        output = "%s standing towards %s (%s)" % (self.standing, self.object_name, self.object_id)
        return output.encode('utf-8')

    def assign_object(self, object):
        if isinstance(object, EVECharacter) or isinstance(object, EVECorporation) or isinstance(object, EVEAlliance):
            self.object_id = object.pk
            self.content_object = object
        else:
            raise TypeError("Standing must be towards object of type EVECharacter, EVECorporation, EVEAlliance.")

    objects = EVEContactManager()
