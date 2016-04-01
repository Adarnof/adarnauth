from __future__ import unicode_literals

from django.db import models
from services.models import BaseServiceModel
import MySQLdb
from authentication.models import User
from django.contrib.auth.models import Group
from passlib.apps import phpbb3_context
import re
import logging
import os
from datetime import datetime
import calendar

logger = logging.getLogger(__name__)

class Phpbb3Service(BaseServiceModel):
    mysql_user = models.CharField(max_length=254)
    mysql_password = models.CharField(max_length=254)
    mysql_database_name = models.CharField(max_length=254)
    mysql_database_host = models.CharField(max_length=254, default='127.0.0.1')
    mysql_database_port = models.PositiveIntegerField(default=3306)

    address = models.CharField(max_length=254)
    revoked_email = models.EmailField(max_length=254)
    set_avatars = models.BooleanField(default=False)

    # SQL commands shamelessly stolen from v1 #
    SQL_ADD_USER = r"INSERT INTO phpbb_users (username, username_clean, " \
                   r"user_password, user_email, group_id, user_regdate, user_permissions, " \
                   r"user_sig) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"

    SQL_DEL_USER = r"DELETE FROM phpbb_users where username = %s"

    SQL_DIS_USER = r"UPDATE phpbb_users SET user_email= %s, user_password=%s WHERE username = %s"

    SQL_USER_ID_FROM_USERNAME = r"SELECT user_id from phpbb_users WHERE username = %s"

    SQL_ADD_USER_GROUP = r"INSERT INTO phpbb_user_group (group_id, user_id, user_pending) VALUES (%s, %s, %s)"

    SQL_GET_GROUP_ID = r"SELECT group_id from phpbb_groups WHERE group_name = %s"

    SQL_ADD_GROUP = r"INSERT INTO phpbb_groups (group_name,group_desc,group_legend) VALUES (%s,%s,0)"

    SQL_UPDATE_USER_PASSWORD = r"UPDATE phpbb_users SET user_password = %s WHERE username = %s"

    SQL_UPDATE_USER_USERNAME = r"UPDATE phpbb_users SET username = %s WHERE user_id = %s"

    SQL_REMOVE_USER_GROUP = r"DELETE FROM phpbb_user_group WHERE user_id=%s AND group_id=%s "

    SQL_GET_ALL_GROUPS = r"SELECT group_id, group_name FROM phpbb_groups"

    SQL_GET_USER_GROUPS = r"SELECT phpbb_groups.group_name FROM phpbb_groups , phpbb_user_group WHERE " \
                          r"phpbb_user_group.group_id = phpbb_groups.group_id AND user_id=%s"

    SQL_ADD_USER_AVATAR = r"UPDATE phpbb_users SET user_avatar_type=2, user_avatar_width=64, user_avatar_height=64, user_avatar=%s WHERE user_id = %s"
    
    SQL_CLEAR_USER_PERMISSIONS = r"UPDATE phpbb_users SET user_permissions = '' WHERE user_Id = %s"    


    def __get_cursor(self):
        db = MySQLdb.connect(user=self.mysql_user, passwd=self.mysql_password, db=self.mysql_database_name, host=self.mysql_database_host, port=self.mysql_database_port)
        return db.cursor()
        
    def __get_current_utc_date():
        d = datetime.utcnow()
        unixtime = calendar.timegm(d.utctimetuple())
        return unixtime

    def __add_avatar(self, user_id, character_id):
        logger.debug("Adding EVE character id %s portrait as phpbb avater for user %s" % (character_id, user_id))
        avatar_url = "http://image.eveonline.com/Character/" + character_id + "_64.jpg"
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_ADD_USER_AVATAR, [avatar_url, user_id])

    def __gen_hash(self, password):
        return phpbb3_context.encrypt(password)

    def __get_all_groups(self):
        logger.debug("Getting all phpbb3 groups.")
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_GET_ALL_GROUPS)
        rows = cursor.fetchall()
        out = {}
        for row in rows:
            out[row[1]] = row[0]
        logger.debug("Got %s phpbb groups" % len(out))
        return out

    def __get_user_groups(self, user_id):
        logger.debug("Getting phpbb3 user id %s groups" % user_id)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_GET_USER_GROUPS, [user_id])
        out = [row[0] for row in cursor.fetchall()]
        logger.debug("Got %s phpbb groups for user_id %s" % (len(out), user_id))
        return out

    def __get_group_id(group_name):
        logger.debug("Getting phpbb3 group id for group_name %s" % group_name)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_GET_GROUP_ID, [group_name])
        row = cursor.fetchone()
        if row is not None:
            logger.debug("Got phpbb group id %s for groupname %s" % (row[0], group_name))
            return row[0]
        else:
            logger.debug("Groupname %s not found on phpbb. Unable to determine group id." % group_name)
            return None

    def __create_group(group_name):
        logger.debug("Creating phpbb3 group %s" % group_name)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_ADD_GROUP, [group_name, group_name])
        logger.info("Created phpbb group %s" % group_name)

    def __get_user_id(self, username):
        logger.debug("Getting phpbb3 user id for username %s" % username)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_USER_ID_FROM_USERNAME, [username])
        row = cursor.fetchone()
        if row is not None:
            logger.debug("Got phpbb user id %s for username %s" % (row[0], username))
            return row[0]
        else:
            logger.error("Username %s not found on phpbb. Unable to determine user id." % username)
            return None

    def __update_username(user_id, username):
        logger.debug("Updating username for phpbb user %s to %s" % (user_id, username))
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_UPDATE_USER_USERNAME, [user_id, username])
        logger.info("Updated phpbb3 user id %s to username %s" % (user_id, username))

    def _add_user_to_group(user_id, group_id):
        logger.debug("Adding phpbb3 user id %s to group id %s" % (user_id, group_id))
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_ADD_USER_GROUP, [group_id, user_id, 0])
        cursor.execute(self.SQL_CLEAR_USER_PERMISSIONS, [user_id])
        logger.info("Added phpbb user id %s to group id %s" % (user_id, group_id))

    def _remove_user_from_group(user_id, group_id):
        logger.debug("Removing phpbb3 user id %s from group id %s" % (user_id, group_id))
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_REMOVE_USER_GROUP, [user_id, group_id])
        cursor.execute(self.SQL_CLEAR_USER_PERMISSIONS, [user_id])
        logger.info("Removed phpbb user id %s from group id %s" % (user_id, group_id))

    def __update_user_info(username, password, email=None):
        if not email:
            email = self.revoked_email
        logger.debug("Updating phpbb user %s info: username %s password of length %s" % (username, email, len(password)))
        pwhash = self.__gen_hash(password)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_DIS_USER, [email, pwhash, username])
        logger.info("Updated phpbb user %s info" % username)

    def __add_user(username, password, email=None):
        logger.debug("Adding phpbb user with username %s" % username)
        cursor = self.__get_cursor()
        pwhash = self.__gen_hash(password)
        cursor.execute(self.SQL_ADD_USER, [username, username, pwhash,
                                                            email, 2, self.__get_current_utc_date(),
                                                            "", ""])
        logger.info("Added phpbb user %s" % username)

    def __lock_user(self, username):
        logger.debug("Disabling phpbb user %s" % username)
        password = self.__generate_random_pass()
        self.__update_user_info(username, password, email=self.revoked_email)

    def _delete_user(self, username):
        logger.debug("Deleting phpbb user %s" % username)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_DEL_USER, [username])
        logger.info("Deleted phpbb user %s" % username)

    def __get_user_groups(self, user_id):
        logger.debug("Getting phpbb3 user id %s groups" % user_id)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_GET_USER_GROUPS, [user_id])
        out = [row[0] for row in cursor.fetchall()]
        logger.debug("Got user %s phpbb groups %s" % (user_id, out))
        return out

    def _update_user_groups(self, user_id, group_ids):
        groups = self.__get_user_groups(user_id)
        for g in groups:
            if g['group_id'] in group_ids is False:
                self.__remove_user_from_group(user_id, g)
        for g in group_ids:
            if g in groups is False:
                self.__add_user_to_group(user_id, g)

    def _check_group_exists_by_name(self, group_name):
        groups = self.__get_all_groups()
        for g in groups:
            if g['group_name']==group_name:
                return True
        return False

    def _check_group_exists_by_id(self, group_id):
        groups = self.__get_all_groups()
        for g in groups:
            if g['group_id']==group_id:
                return True
        return False

    def test_connection(self):
        try:
            self.__get_cursot()
            return True
        except:
            return False

    def add_user(self, user, password=None):
        if Phpbb3User.objects.filter(user=user).filter(service=self).exists():
            user_model = Phpbb3User.objects.get(user=user, service=self)
            logger.error("User %s already has user account on phpbb service %s" % (user, self))   
            return
        if self.check_user_has_access(user) is False:
            logger.error("User %s does not meet group requirements for phpbb service %s" % (user, self))
            return
        username = self.__sanatize_username(str(user))
        logger.debug("Adding user %s to phpbb service %s with username %s" % (user, self, username))
        if not password:
            logger.debug("No password supplied. Generating random.")
            password = self._generate_random_pass()
        self.__add_user(username, password)
        user_id = self.__get_user_id(username)
        if user_id:
            if self.set_avatars:
                self.__add_avatar(user_id, user.main_character_id)
            user_model = Phpbb3User(user=user, username=username, user_id=user_id, service=self)
            logger.info("Creating Phpbb3User model for user %s on service %s" % (user, self))
            user_model.save()
        else:
            logger.error("Failed to add user %s to phpbb service %s" % (user, self))

    def remove_user(self, user):
        if Phpbb3User.objects.filter(user=user).filter(service=self).exists():
            user_model = Phpbb3User.objects.get(user=user, service=service)
            logger.info("Removing user %s from phpbb service %s" % (user, self))
            user_model.delete()
        else:
            logger.error("User %s not found on phpbb service %s - unable to remove." % (user, self))

    def set_password(self, user, password=None):
        if Phpbb3User.objects.filter(user=user).filter(servive=self).exists():
            user_model = Phpbb3User.objects.get(user=user, service=service)
            if not password:
                password = self._generate_random_pass()
            logger.info("Updating user %s password on phpbb service %s" % (user, self))
            self.__update_user_info(user_model.username, password)
        else:
            logger.error("User %s not found on phpbb service %s - unable to update password." % (user, self))

    def get_display_parameters(self, user):
        if Phpbb3User.objects.filter(user=user).filter(service=self).exists():
            user_model = Phpbb3User.objects.get(user=user, service=self)
            username = user_model.username
            address = self.address
            active = True
        else:
            username = None
            address = None
            active = False
        return {'username':username, 'address':address, 'active':active}

    def sync_groups(self):
        phpbb_groups = self.__get_all_groups()
        logger.debug("Received %s groups on Phpbb service %s" % (len(phpbb_groups), self))
        for g in phpbb_groups:
            if Phpbb3Group.objects.filter(service=self).filter(group_id=g['group_id']).exists() is False:
                logger.info("Creating model for new group %s on phpbb service %s" % (g, self))
                group_model = Phpbb3Group(service=self, group_id=g['group_id'], group_name=g['group_name'])
                group_model.save()
        for g in Phpbb3Group.objects.filter(service=self):
            if g.group_id in phpbb_groups is False:
                logger.info("Deleting model for missing group %s on phpbb service %s" % (g, self))
                g.delete()
        for g in phpbb_groups:
            group_model = Phpbb3Group.objects.get(group_id=g['group_id'], service=self)
            if group_model.group_name != g['group_name']:
                logger.info("Updating name of phpbb group %s on service %s to %s" % (group_model, self, g['group_name']))
                group_model.group_name = g['group_name']
                group_model.save(update_fields['group_name'])

    def update_user_groups(self, user):
        if Phpbb3User.objecs.filter(user=user).filter(service=self).exists():
            user_model = Phpbb3User.objects.get(user=user, service=service)
            for g in user.groups.all():
                for p in g.phpbb3group_set.all():
                    if not p in user_model.phpbb3_groups.all():
                        user_model.phpbb3_groups.add(p)
            for p in user_model.phpbb3_groups.all():
                for g in p.groups.all():
                    if g in user.groups.all():
                        break
                else:
                    user_model.phpbb3_groups.remove(p)

    def update_user_username(self, user):
        if Phpbb3User.objecs.filter(user=user).filter(service=self).exists():
            user_model = Phpbb3User.objects.get(user=user, service=service)
            username = self.__sanatize_username(str(user))
            self.__update_username(user_model.user_id, username)

    def create_group(self, group_name):
        safe_name = self.__sanatize_username(group_name)
        if Phpbb3Group.objects.filter(group_name=safe_name).exists():
            logger.error("Attempting to duplicate existing group %s on phpbb service %s" % (group_name, self))
        else:
            logger.info("Creating group %s on phpbb service %s" % (safe_name, self))
            self.__create_group(group_name)
        self.sync_groups()

    def auto_configure_groups(self):
        logger.debug("Initiating auto-configuration of groups for phpbb service %s" % self)
        self.sync_groups()
        for g in Group.objects.all():
            safe_name = self.__sanatize_username(g.name)
            if Phpbb3Group.objects.filter(service=self).filter(group_name=safe_name).exists() is False:
                logger.info("Auto-generating group on phpbb service %s for group %s" % (self, g))
                self.create_group(safe_name)
                model = Phpbb3Group.objects.get(service=self, group_name=safe_name)
                model.groups.add(g)

class Phpbb3Group(models.Model):
    service = models.ForeignKey(Phpbb3Service, on_delete=models.CASCADE, editable=False)
    groups = models.ManyToManyField(Group)
    group_id = models.PositiveIntegerField(editable=False)
    group_name = models.CharField(max_length=254, editable=False)

    class Meta:
        unique_together = ("group_id", "service")

    def __unicode__(self):
        output = "%s group %s" % (self.service, self.group_name)
        return output.encode('utf-8')

class Phpbb3User(models.Model):
    service = models.ForeignKey(Phpbb3Service, on_delete=models.CASCADE, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, editable=False)
    phpbb_user_id = models.PositiveIntegerField(editable=False)
    phpbb_username = models.CharField(max_length=254, editable=False)
    phpbb_groups = models.ManyToManyField(Phpbb3Group, blank=True)

    class Meta:
        unique_together = ("user", "service")

    def __unicode__(self):
        output = "%s user %s" % (self.service, self.user)
        return output.encode('utf-8')
