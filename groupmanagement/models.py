from __future__ import unicode_literals
from django.contrib.auth.models import Group
from authentication.models import User
from django.utils import timezone
from django.db import models
from managers import GroupApplicationManager
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType

class ExtendedGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE)
    admins = models.ManyToManyField(User, related_name='admin_groups', blank=True)
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

class GroupApplication(models.Model):
    extended_group = models.ForeignKey(ExtendedGroup, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    response = models.NullBooleanField(blank=True)
    
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
    group = models.OneToOneField(Group, on_delete=models.CASCADE, unique=True)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
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
