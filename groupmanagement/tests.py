from django.test import TestCase
from .models import ExtendedGroup
from django.contrib.auth.models import Group, Permission
from authentication.models import User
from access.signals import user_loses_access
from django.contrib.contenttypes.models import ContentType


class ExtendedGroupTestCase(TestCase):
    owner_id = 94677678
    admin_id = 234899860
    def setUp(self):
        self.owner = User.objects.create_user(main_character_id=self.owner_id)
        self.admin = User.objects.create_user(main_character_id=self.admin_id)
        self.group, c = Group.objects.get_or_create(name='Test Group Please Ignore')
        self.exgroup, c = ExtendedGroup.objects.get_or_create(owner=self.owner, group=self.group)
        self.perm, c = Permission.objects.get_or_create(content_type=ContentType.objects.get_for_model(ExtendedGroup), codename='can_manage_groups')

    def test_owner_loses_access_no_admins(self):
        #ensures extendedgroup and group get deleted when can't assign new owner
        user_loses_access.send(sender=TestCase, user=self.owner)
        self.assertFalse(Group.objects.filter(name=self.group.name))
        self.assertFalse(ExtendedGroup.objects.filter(group=self.group))

    def test_owner_loses_access_invalid_admins(self):
        #ensures extendedgroup and group get deleted when can't assign new owner
        self.exgroup.admins.add(self.admin)
        user_loses_access.send(sender=TestCase, user=self.owner)
        self.assertFalse(Group.objects.filter(name=self.group.name))
        self.assertFalse(ExtendedGroup.objects.filter(group=self.group))

    def test_owner_loses_access_admin_has_perm(self):
        self.admin.user_permissions.add(self.perm)
        self.exgroup.admins.add(self.admin)
        user_loses_access.send(sender=TestCase, user=self.owner)
        #ensure group and exgroup still exist
        self.assertTrue(Group.objects.filter(name=self.group.name))
        self.assertTrue(ExtendedGroup.objects.filter(group=self.group))
        #ensure new owner is old admin
        self.exgroup.refresh_from_db()
        self.assertEqual(self.exgroup.owner, self.admin)
        #ensure new owner not still listed as admin
        self.assertFalse(self.admin in self.exgroup.admins.all())
        #ensure old owner not in group
        self.assertFalse(self.group in self.owner.groups.all())
