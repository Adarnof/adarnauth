from __future__ import unicode_literals

from django.db import models
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance, EVEContactSet, EVEContact
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from authentication.models import User
import logging

logger = logging.getLogger(__name__)

class BaseAccessRule:
    def _validate_rule(self, characters, useraccess):
        for char in characters:
            if not char.user:
                logger.debug("Access rule for %s applies to character %s but they have no user." % (self, char))
            elif useraccess.filter(character=char).exists():
                logger.debug("Acces rule for  %s already applied to character %s" % (self, char))
            else:
                logger.info("Applying access rule for %s to user %s through character %s" % (self, char.user, char))
                ua = UserAccess(user=char.user, character=char)
                ua.set_rule(self)
                ua.save()
        for ua in useraccess:
            if not ua.character in characters:
                logger.info("Acess rule for %s no longer applies to %s because %s is not in alliance" % (self, ua.user, ua.character))
                ua.delete()
                continue
            if ua.character.user != ua.user:
                logger.info("Access rule for %s no longer applies to %s because UserAccess and Character %s users don't match" % (self, ua.user, ua.character))
                ua.delete()
                continue
            logger.debug("UserAccess %s confirmed still valid." % ua)
        logger.debug("Completed validating access rule for %s" % self)


class CorpAccessRule(models.Model, BaseAccessRule):

    corp = models.OneToOneField(EVECorporation, models.CASCADE)
    access = GenericRelation('access.UserAccess')
    auto_group = GenericRelation('groupmanagement.AutoGroup')

    def __unicode__(self):
        output = 'corp %s' % self.corp
        return output.encode('utf-8')

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by CorpAccess rule %s" % self)
        characters = EVECharacter.objects.filter(corp_id=self.corp.id)
        useraccess = self.access.all()
        self._validate_rule(characters, useraccess)

class AllianceAccessRule(models.Model, BaseAccessRule):

    alliance = models.OneToOneField(EVEAlliance, models.CASCADE)
    access = GenericRelation('access.UserAccess')
    auto_group = GenericRelation('groupmanagement.AutoGroup')

    def __unicode__(self):
        output = 'alliance %s' % self.alliance
        return output.encode('utf-8')

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by AllianceAccess rule %s" % self)
        characters = EVECharacter.objects.filter(alliance_id=self.alliance.id)
        useraccess = self.access.all()
        self._validate_rule(characters, useraccess)

class CharacterAccessRule(models.Model, BaseAccessRule):

    character = models.OneToOneField(EVECharacter, models.CASCADE)
    access = GenericRelation('access.UserAccess')
    auto_group = GenericRelation('groupmanagement.AutoGroup')

    def __unicode__(self):
        output = 'character %s' % self.character
        return output.encode('utf-8')

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by CharacterAccess rule %s" % self)
        characters = EVECharacter.objects.filter(id=self.character.id)
        useraccess = self.access.all()
        self._validate_rule(characters, useraccess)

class StandingAccessRule(models.Model):
    standings = models.OneToOneField(EVEContactSet, models.CASCADE)

    def __unicode__(self):
        return "%s" % self.standings

    def generate_contactaccess(self):
        for contact in self.standings.contacts.all():
            if ContactAccess.objects.filter(contact=contact).filter(standing_access=self).exists() is False:
                logger.info("Creating ContactAccess for %s from %s" % (contact, self))
                ca = ContactAccess(contact=contact, standing_access=self)
                ca.save()
        for ca in self.contactaccess_set.all():
            if ca.contact in self.standings.contacts.all() is False:
                logger.info("Deleting %s from %s as the contact no longer exists" % (ca, self))

    def generate_useraccess(self):
        for ca in self.contactaccess_set.all():
            ca.generate_useraccess()

class ContactAccess(models.Model, BaseAccessRule):
    contact = models.ForeignKey(EVEContact, on_delete=models.CASCADE)
    standing_access = models.ForeignKey(StandingAccessRule, on_delete=models.CASCADE)
    access = GenericRelation('access.UserAccess')

    attrs = ['id', 'corp_id', 'alliance_id', 'faction_id']

    class Meta:
        unique_together = (('contact', 'standing_access'),)

    def __unicode__(self):
        return "%s from API" % self.contact

    def check_if_applies_to_character(self, char):
        for attr in self.attrs:
            if getattr(char, attr) == self.contact.object_id:
                logger.debug("%s applies to %s by attribute %s" % (self, char, attr))
                return True
        logger.debug("%s does not apply to %s" % (self, char))
        return False

    def __get_applicable_characters(self):
        chars = set([])
        for attr in self.attrs:
            kwargs = {attr:self.contact.object_id}
            for char in EVECharacter.objects.filter(**kwargs):
                chars.add(char)
        logger.debug("%s applies to %s characters" % (self, len(chars)))
        return chars

    def generate_useraccess(self):
        ct = ContentType.objects.get_for_model(self)
        logger.debug("Assigning UserAccess by ContactAccess %s from %s" % (self, self.standing_access))
        useraccess = self.access.all()
        characters = self.__get_applicable_characters()
        self._validate_rule(characters, useraccess)

RULE_CONTENT_TYPES = [
    ContentType.objects.get_for_model(AllianceAccessRule),
    ContentType.objects.get_for_model(CorpAccessRule),
    ContentType.objects.get_for_model(CharacterAccessRule),
    ContentType.objects.get_for_model(ContactAccess),
    ]

def get_rule_ct_filter():
    return {'pk__in': [a.pk for a in RULE_CONTENT_TYPES]}

class UserAccess(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=get_rule_ct_filter)
    access_rule = GenericForeignKey('content_type', 'object_id')
    character = models.ForeignKey(EVECharacter, on_delete=models.CASCADE)

    def __unicode__(self):
        output = '%s access by rule for %s applying to %s' % (self.user, self.access_rule, self.character)
        return output.encode('utf-8')

    class Meta:
        permissions = (("site_access", "User has access to site."), ("manage_access", "User can manage site access."), ("audit_access", "User can view access granted per rule."))
        verbose_name_plural = "User access"

    def set_rule(self, object):
        if ContentType.objects.get_for_model(object) in RULE_CONTENT_TYPES:
            self.object_id = object.pk
            self.access_rule = object
        else:
            raise TypeError("Access rule must be of type %s" % RULE_CONTENT_TYPES)

    def get_rule(self):
        return self.access_rule

    def verify(self):
        self.save()
