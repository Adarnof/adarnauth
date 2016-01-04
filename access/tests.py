from django.test import TestCase
from .models import UserAccess, CharacterAccessRule, CorpAccessRule, AllianceAccessRule
from authentication.models import User
from eveonline.managers import EVEManager
import os
from .tasks import generate_useraccess_by_characteraccess, generate_useraccess_by_corpaccess, generate_useraccess_by_allianceaccess

class UserAccessAssignmentTestCase(TestCase):
    good_char_id = 94677678
    bad_char_id = 234899860
    corp_id = 98317560
    alliance_id = 99004485
    def setUp(self):
        self.good_user = User.objects.create_user(main_character_id=self.good_char_id)
        self.bad_user = User.objects.create_user(main_character_id=self.bad_char_id)
        self.char = EVEManager.get_character_by_id(self.good_char_id)
        self.corp = EVEManager.get_corp_by_id(self.corp_id)
        self.alliance = EVEManager.get_alliance_by_id(self.alliance_id)
    
    def test_create_characteraccess(self):
        #ensure useraccess generated for correct user upon creation of characteraccess rule
        ca = CharacterAccessRule.objects.create(character=self.char)
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
