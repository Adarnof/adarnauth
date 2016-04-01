from __future__ import unicode_literals

from django.db import models
from services.models import BaseServiceModel
from authentication.models import User
from django.contrib.auth.models import Group
import logging
import ofrestapi

logger = logging.getLogger(__name__)

class OpenfireService(BaseServiceModel):
    restapi_address = models.CharField(max_length=254)
    restapi_secret_key = models.CharField(max_length=254)

    address = models.CharField(max_length=254)
    port = models.PositiveIntegerField()

    def _delete_user(self, username):
        api = ofrestapi.users.Users(self.restapi_address, self.restapi_secret_key)
        api.delete_user(username)

    def _add_user(self, username, password):
        api = ofrestapi.users.Users(self.restapi_address, self.restapi_secret_key)
        api.add_user(username, password)

    def _add_user_to_groups(self, username, groups):
        api = ofrestapi.users.Users(self.restapi_address, self.restapi_secret_key)
        api.add_user_groups(username, groups)

    def _remove_user_from_groups(self, username, groups):
        api = ofrestapi.users.Users(self.restapi_address, self.restapi_secret_key)
        api.delete_user_groups(username, groups)

    def __get_user_groups(self, username):
        api = ofrestapi.users.Users(self.restapi_address, self.restapi_secret_key)
        return api.get_user_groups(username)

    def _update_user_groups(self, username, groups):
        of_groups = self.__get_user_groups(username)
        rem_groups = []
        add_groups = []
        for g in of_groups:
            if g in groups is False:
                rem_groups.add(g)
        for g in groups:
            if g in of_groups is False:
                add_groups.add(g)
        if rem_groups:
            self._remove_user_from_groups(username, rem_groups)
        if add_groups:
            self._add_user_to_groups(username, add_groups)

    def test_connection(self):
        try:
            api = ofresapi.users.Users(self.restapi_address, self.restapi_secret_key)
            return True
        except:
            return False

    def sync_groups(self):
        api = ofrestapi.groups.Groups(self.restapi_address, self.restapi_secret_key)
        of_groups = api.get_groups()
        for g in of_groups:
            if OpenfireGroup.objects.filter(service=self, group_name=g).exists() is False:
                logger.info("Creating model for new group %s on openfire service %s" % (g, self))
                group_model = OpenfireGroup(service=self, group_name=g)
                group_model.save()
        for g in OpenfireGroup.objects.filter(service=self):
            if g.group_name in of_groups is False:
                logger.info("Deleting model for missing group %s on openfire service %s" % (g, self))
                g.delete()

    def update_user_groups(self, user):
        if OpenfireUser.objects.filter(service=self).filter(user=user).exists():
            user_model = OpenfireUser.objects.get(service=self, user=user)
            for g in user.groups.all():
                for o in g.openfiregroup_set.all():
                    if o in user_model.openfire_groups.all() is False:
                        user_model.openfire_groups.add(o)
            for o in user_model.openfire_groups.all():
                for g in o.groups:
                    if g in user.groups.all():
                        break
                else:
                    user_model.groups.remove(o)

    def create_group(self, group_name):
        safe_name = self.__sanatize_username(group_name)
        if OpenfireGroup.objects.filter(service=self).filter(group_name=safe_name).exists():
            logger.error("Attempting to duplicate existing group %s on openfire service %s" % (group_name, self))
        else:
            logger.info("Creating group %s on openfire service %s" % (safe_name, self))
            api = ofrestapi.groups.Groups(self.restapi_address, self.restapi_secret_key)
            api.add_group(safe_name, None)
            self.sync_groups()

    def auto_configure_groups(self):
        logger.debug("Initiating auto-configuration of groups for openfire service %s" % self)
        self.sync_groups()
        for g in Group.objects.all():
            safe_name = self.__sanatize_groupname(g.name)
            if OpenfireGroup.objects.filter(service=self).filter(group_name=safe_name).exists() is False:
                logger.info("Auto-generating group on openfire service %s for group %s" % (self, g))
                self.create_group(safe_name)
                model = OpenfireGroup.objects.get(service=self, group_name=safe_name)
                model.groups.add(g)

    def add_user(self, user, password=None):
        if OpenfireUser.objects.filter(service=self).filter(user=user).exists():
            logger.error("User %s already has user account on openfire service %s" % (user, self))
            return
        if self.check_user_has_access(user) is False:
            logger.error("User %s does not meet group requirements for openfire service %s" % (user, self))
            return
        username = self.__sanatize_username(str(user))
        logger.debug("Adding user %s to openfire service %s with username %s" % (user, self, username))
        if not password:
            logger.debug("No password supplied. Generating random.")
            password = self._generate_random_pass()
        self._add_user(username, password)
        logger.info("Creating OpenfireUser model for user %s on service %s" % (user, self))
        user_model = OpenfireUser(user=user, username=username, service=self)
        user_model.save()

    def remove_user(self, user):
        if OpenfireUser.objects.filter(service=self).filter(user=user).exists():
            user_model = OpenfireUser.objects.get(service=self, user=user)
            logger.info("Removing user %s from openfire service %s" % (user, self))
            user_model.delete()
        else:
            logger.error("User %s not found on openfire service %s - unable to remove." % (user, self))

    def set_password(self, user, password=None):
        if OpenfireUser.objects.filter(service=self).filter(user=user).exists():
            user_model = OpenfireUser.objects.get(service=self, user=user)
            if not password:
                password = self._generate_random_pass()
            logger.info("Updating user %s password on openfire service %s" % (user, self))
            api = ofrestapi.users.Users(self.restapi_address, self.restapi_secret_key)
            api.update_user(user_model.username, password=password)

    def get_display_parameters(self, user):
        if OpenfireUser.objects.filter(service=self).filter(user=user).exists():
            user_model = OpenfireUser.objects.get(service=self, user=user)
            username = user_model.username
            address = "%s:%s" % (self.address, self.port)
            active = True
        else:
            username = None
            address = None
            active = False
        return {'username':username, 'address':address, 'active':active}
        

class OpenfireGroup(models.Model):
    service = models.ForeignKey(OpenfireService, on_delete=models.CASCADE)
    group_name = models.CharField(max_length=254)
    groups = models.ManyToManyField(Group)

    class Meta:
        unique_together = ('service', 'group_name')

    def __unicode__(self):
        output = "%s group %s" % (self, self.group_name)
        return output.encode('utf-8')

class OpenfireUser(models.Model):
    service = models.ForeignKey(OpenfireService, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    username = models.CharField(max_length=254)
    openfire_groups = models.ManyToManyField(OpenfireGroup, blank=True)

    class Meta:
        unique_together = ('service', 'user')

    def __unicode__(self):
        output = "%s user %s" % (self, self.user)
        return output.encode('utf-8')
