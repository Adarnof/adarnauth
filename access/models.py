from __future__ import unicode_literals

from django.db import models
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance, EVEStanding
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from authentication.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)

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
    def set_rule(self, object):
        if isinstance(object, CharacterAccess) or isinstance(object, CorpAccess) or isinstance(object, AllianceAccess) or isinstance(object, StandingAccess):
            self.object_id = object.pk
            self.content_object = object
        else:
            raise TypeError("Access rule must be of type CharacterAccess, CorpAccess, AllianceAccess, StandingAccess.")
    def get_rule(self):
        return self.content_object

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

@receiver(post_delete, sender=UserAccess)
def post_delete_useraccess(sender, instance, *args, **kwargs):
    if instance.user:
        logger.info("Received post_delete signal from UserAccess models %s. Triggering assessment of user %s access rights." % (instance, instance.user))
        from tasks import assess_access
        assess_access.delay(user)
    else:
        logger.info("Received post_delete signal from UserAccess model %s. No affiliated user found. Ignoring." % instance)
