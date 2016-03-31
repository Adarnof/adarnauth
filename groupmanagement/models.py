from __future__ import unicode_literals
from django.contrib.auth.models import Group
from authentication.models import User
from django.utils import timezone
from django.db import models
from managers import GroupApplicationManager, ExtendedGroupManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from access.models import get_rule_ct_filter

def get_group_manager_choices():
    choices = []
    for u in User.objects.all():
        if u.has_perm('groupmanagement.can_manage_groups'):
            choices.append(u.pk)
    return {'pk__in': choices}

def get_base_group_choices():
    choices = []
    for g in Group.objects.all():
        if not AutoGroup.objects.filter(group=g).exists():
            choices.append(g.pk)
    return {'pk__in': choices}

def get_auto_group_choices():
    choices = []
    for g in Group.objects.all():
        if not ExtendedGroup.objects.filter(group=g).exists():
            choices.append(g.pk)
    return {'pk__in': choices}

class ExtendedGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, limit_choices_to=get_base_group_choices)
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE, limit_choices_to=get_group_manager_choices)
    admins = models.ManyToManyField(User, related_name='admin_groups', blank=True, limit_choices_to=get_group_manager_choices)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='child_groups', blank=True)
    hidden = models.BooleanField(default=False, blank=True)
    description = models.CharField(max_length=254, null=True, blank=True)
    require_application = models.BooleanField(default=False, blank=True)

    @property
    def name(self):
        return self.group.name

    def __unicode__(self):
        return self.name.encode('utf-8')

    def get_members(self):
        return User.objects.filter(groups__name__in=[self.name])

    class Meta:
        permissions = (("can_manage_groups", "Can own or administrate groups."),)

    objects = ExtendedGroupManager()

    def get_possible_admins(self):
        admins = []
        for u in self.group.user_set.exclude(pk=self.owner.pk):
            if u.has_perm('groupmanagement.can_manage_groups'):
                admins.append(u)
        return admins

    def get_possible_owners(self):
        return self.admins.exclude(pk=self.owner.pk)

    def is_visible_to_user(self, user):
        if user.is_superuser:
            return True
        elif user in self.group.user_set.all():
            return True
        elif not self.hidden:
            if self.parent and self.parent in user.groups.all():
                return True
        return False

    def can_promote_member(self, user, member):
        if user == self.owner:
            if member in self.get_possible_admins() and not user in self.admins.all() and not user == self.owner:
                return True
        return False

    def can_demote_admin(self, user, admin):
        if user == self.owner and admin in self.admins.all():
            return True
        elif user == admin and user in self.admins.all():
            return True
        return False

    def can_leave_group(self, user):
        if user == self.owner:
            return False
        elif user in self.admins.all():
            return False
        return True

    def can_remove_member(self, user, member):
        if member == self.owner:
            return False
        elif member in self.admins.all():
            return False
        elif user == self.owner or user in self.admins.all():
            return True

    @property
    def basic_members(self):
        return [u for u in self.group.user_set.all() if u != self.owner and u not in self.admins.all()]

class GroupApplication(models.Model):
    extended_group = models.ForeignKey(ExtendedGroup, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    response = models.NullBooleanField(blank=True)
    
    class Meta:
        unique_together = ('extended_group', 'user')

    def __unicode__(self):
        output = "%s application to %s" % (self.user, self.group)
        return output.encode('utf-8')

    def accept(self):
        self.response = True
        self.responded = timezone.now()
        self.save(update_fields=['response'])

    def reject(self):
        self.response = False
        self.responded = timezone.now()
        self.save(update_fields=['response'])

    @property
    def group(self):
        return self.extended_group.group

    objects = GroupApplicationManager()

class AutoGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, limit_choices_to=get_auto_group_choices)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to=get_rule_ct_filter)
    access_rule = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        output = "AutoGroup %s for %s" % (self.group, self.access_rule)
        return output.encode('utf-8')

    def set_rule(self, object):
        self.object_id = object.pk
        self.access_rule = object

    class Meta:
        unique_together = ('content_type', 'object_id')
        permissions = (('manage_autogroups', 'User can manage auto groups'),)
