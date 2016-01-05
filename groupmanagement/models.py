from __future__ import unicode_literals
from django.contrib.auth.models import Group
from authentication.models import User

from django.db import models

class ExtendedGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE)
    admins = models.ManyToManyField(User, related_name='admin_groups', blank=True)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='child_groups', blank=True)
    hidden = models.BooleanField(default=False, blank=True)
    description = models.CharField(max_length=254, null=True, blank=True)

    @property
    def name(self):
        return self.group.name

    def __unicode__(self):
        return self.name.encode('utf-8')

    def get_members(self):
        return User.objects.filter(groups__name__in=[self.name])
