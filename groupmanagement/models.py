from __future__ import unicode_literals
from django.contrib.auth.models import Group
from authentication.models import User

from django.db import models

class ExtendedGroup(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, related_name='owned_groups', on_delete=models.CASCADE)
    admins = models.ManyToManyField(User, related_name='admin_groups')
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL, related_name='child_groups')
    hidden = models.BooleanField(default=False)

    @property
    def name(self):
        return self.group.name

    def __unicode__(self):
        return self.name.encode('utf-8')
