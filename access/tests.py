from django.test import TestCase
from .models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule
from authentication.models import User
from eveonline.managers import EVEManager
from eveonline.models import EVECharacter, EVECorporation, EVEAlliance
import os
from .tasks import generate_useraccess_by_characteraccess, generate_useraccess_by_corpaccess, generate_useraccess_by_allianceaccess, assess_access, assign_access
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
import logging

logger = logging.getLogger(__name__)

class UserAccessAssignmentTestCase(TestCase):
    good_char_id = 94677678
    bad_char_id = 234899860
    corp_id = 98317560
    alliance_id = 99004485
    def __init__(self, *args, **kwargs):
        super(UserAccessAssignmentTestCase, self).__init__(*args, **kwargs)
        self.good_user = User.objects.create_user(main_character_id=self.good_char_id)
        self.bad_user = User.objects.create_user(main_character_id=self.bad_char_id)
        self.char = EVECharacter(id=self.good_char_id, corp_id=self.corp_id)
        self.corp = EVECorporation(id=self.corp_id)
        self.alliance = EVEAlliance(id=self.alliance_id)
        self.char.save()
        self.corp.save()
        self.alliance.save()
        self.perm, c = Permission.objects.get_or_create(content_type=ContentType.objects.get_for_model(UserAccess), codename='site_access')

    def setUp(self):
        self.good_user.user_permissions.remove(self.perm)
        self.bad_user.user_permissions.remove(self.perm)
    
    def test_create_characteraccess(self):
        logger.debug("-----------------------------------------")
        logger.debug("      test_create_characteraccess")
        logger.debug("-----------------------------------------")
        #ensure useraccess generated for correct user upon creation of characteraccess rule
        ca = CharacterAccessRule(character=self.char)
        ca.save()
        #can't be sure celery is running. Manually calling task.
        generate_useraccess_by_characteraccess(ca)
        self.assertEqual(len(self.good_user.useraccess_set.all()), 1)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)
        #ensure useraccess generated for user removed upon characteraccess rule deletion
        ca.delete()
        self.assertEqual(len(self.good_user.useraccess_set.all()), 0)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)

    def test_create_corpaccess(self):
        logger.debug("-----------------------------------------")
        logger.debug("        test_create_corpaccess")
        logger.debug("-----------------------------------------")
        #ensure useraccess generated for correct user upon creation of corpaccess rule
        ca = CorpAccessRule.objects.create(corp=self.corp)
        ca.save()
        #can't be sure celery is running. Manually calling task.
        generate_useraccess_by_corpaccess(ca)
        self.assertEqual(len(self.good_user.useraccess_set.all()), 1)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)
        #ensure useraccess generated for user removed upon corpaccess rule deletion
        ca.delete()
        self.assertEqual(len(self.good_user.useraccess_set.all()), 0)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)

    def test_create_allianceaccess(self):
        logger.debug("-----------------------------------------")
        logger.debug("      test_create_allianceaccess")
        logger.debug("-----------------------------------------")
        #ensure useraccess generated for correct user upon creation of allianceaccess rule
        aa = AllianceAccessRule.objects.create(alliance=self.alliance)
        aa.save()
        #can't be sure celery is running. Manually calling task.
        generate_useraccess_by_allianceaccess(aa)
        self.assertEqual(len(self.good_user.useraccess_set.all()), 1)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)
        #ensure useraccess generated for user removed upon allianceaccess rule deletion
        aa.delete()
        self.assertEqual(len(self.good_user.useraccess_set.all()), 0)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)

    def test_assign_all_useraccess(self):
        logger.debug("-----------------------------------------")
        logger.debug("      test_assign_all_useraccess")
        logger.debug("-----------------------------------------")
        #generate access rules for all 3 levels
        CharacterAccessRule.objects.create(character=self.char).save()
        CorpAccessRule.objects.create(corp=self.corp).save()
        AllianceAccessRule.objects.create(alliance=self.alliance).save()
        #run full assessment for good user
        assign_access(self.good_user)
        self.assertEqual(len(self.good_user.useraccess_set.all()), 3)
        self.assertTrue(self.perm in self.good_user.user_permissions.all())
        #run full assessment for bad user
        assign_access(self.bad_user)
        self.assertEqual(len(self.bad_user.useraccess_set.all()), 0)        
        self.assertFalse(self.perm in self.bad_user.user_permissions.all())
