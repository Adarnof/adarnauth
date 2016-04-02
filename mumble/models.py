from __future__ import unicode_literals

from django.db import models
from services.models import BaseServiceModel
from django.contrib.auth.models import Group
import hashlib
from authentication.models import User
import services.errors
import logging

logger = logging.getLogger(__name__)

class MumbleService(BaseServiceModel):
    address = models.CharField(max_length=254)
    port = models.PositiveIntegerField(default=65535)

    def _hash(self, username, password):
        return hashlib.sha1(username+password).hexdigest()

    def test_connection(self):
        return True

    def sync_groups(self):
        pass

    def update_user_groups(self, user):
        if MumbleUser.objects.filter(service=self).filter(user=user).exists():
            user_model = MumbleUser.objects.get(service=self, user=user)
            for g in user.groups.all():
                for m in g.mumblegroup_set.filter(service=self):
                    if not m in user_model.mumble_groups.all():
                        user_model.mumble_groups.add(m)
            for m in user_model.mumble_groups.all():
                for g in m.groups.all():
                    if g in user.groups.all():
                        break
                else:
                    user_model.groups.remove(m)

    def create_group(self, group_name):
        safe_name = self.__sanatize_username(group_name)
        if MumbleGroup.objects.filter(service=self).filter(group_name=safe_name).exists():
            raise services.errors.DuplicateGroupError(self, None, safe_name)
        else:
            logger.info("Creating group %s on mumble service %s" % (safe_name, self))
            model = MumbleGroup(group_name=safe_name, service=self)
            model.save()
            return model

    def auto_configure_groups(self):
        logger.debug("Initiating auto-configuration of groups for mumble service %s" % self)
        for g in Group.objects.all():
            safe_name = self.__sanatize_username(g.name)
            if MumbleGroup.objects.filter(group_name=safe_name).filter(service=self).exists() is False:
                model = self.create_group(g.name)
                model.groups.add(g)

    def add_user(self, user, password=None):
        if MumbleUser.objects.filter(user=user).filter(service=self).exists():
            logger.error("User %s already has user account on mumble service %s" % (user, self))
        if self.check_user_has_access(user) is False:
            raise services.errors.RequiredGroupsError(self, None, user)
        if not password:
            logger.debug("No password supplied. Generating random.")
            password = self._generate_random_pass()
        model = MumbleUser.objects.create(service=self, username=str(user), pwhash=self._hash(str(user), password), user=user)
        return {'username': str(user), 'password': password}

    def remove_user(self, user):
        user_model = MumbleUser.objects.get(service=self, user=user)
        logger.info("Removing user %s from mumble service %s" % (user, self))
        user_model.delete()

    def set_password(self, user, password=None):
        user_model = MumbleUser.objects.get(service=self, user=user)
        if not password:
            password = self._generate_random_pass()
        logger.info("Updating user %s password on mumble service %s" % (user, self))
        user_model.pwhash = self._hash(user_model.username, password)
        user_model.save(update_fields=['pwhash'])
        return {'username': user_model.username, 'password': password}

    def get_display_parameters(self, user):
        if MumbleUser.objects.filter(service=self).filter(user=user).exists():
            user_model = MumbleUser.objects.get(service=self, user=user)
            username = user_model.username
            address = "%s:%s" % (self.address, self.port)
            return {'username':username, 'address':address}
        else:
            return {}

class MumbleGroup(models.Model):
    service = models.ForeignKey(MumbleService, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=254)
    groups = models.ManyToManyField(Group, blank=True)

    class Meta:
        unique_together = ('service', 'group_name')

    def __str__(self):
        output = "%s group %s" % (self.service, self.group_name)
        return output.encode('utf-8')

class MumbleUser(models.Model):
    service = models.ForeignKey(MumbleService, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=254)
    mumble_groups = models.ManyToManyField(MumbleGroup, blank=True)
    pwhash = models.CharField(max_length=128)

    class Meta:
        unique_together = ('service', 'user')

    def __str__(self):
        output = "%s user %s" % (self.service, self.user)
        return output.encode('utf-8')
