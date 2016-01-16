from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import Group
import re
import os

class BaseServiceModel(models.Model):
    name = models.CharField(max_length=254)
    required_groups = models.ManyToManyField(Group)

    def __santatize_username(self, username):
        return re.sub(r'[^\w+]+', '_', username) 
    
    def __generate_random_pass(self):
        return os.urandom(8).encode('hex')

    def add_user(self, user):
        raise NotImplementedError

    def remove_user(self, user):
        raise NotImplementedError

    def update_user_groups(self, user):
        raise NotImplementedError

    def auto_configure_groups(self):
        raise NotImplementedError

    def sync_groups(self):
        raise NotImplementedError

    def create_group(self, group_name):
        raise NotImplementedError

    def set_password(self, user, password=None):
        raise NotImplementedError

    def test_connection(self):
        raise NotImplementedError

    def get_display_parameters(self):
        raise NotImplementedError

    def check_user_has_access(self, user):
        if user.has_perm('access.site_access'):
            if self.required_groups.all().exists():
                if self.required_groups.all() in user.groups.all():
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False            

    def __unicode__(self):
        return self.name.encode('utf-8')

    class Meta:
        abstract = True
