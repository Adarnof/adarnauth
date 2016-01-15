from __future__ import unicode_literals

from django.db import models
from services.models import BaseServiceModel
import MySQLdb
from authentication.models import User, Group
from passlib.apps import phpbb3_context
import re
import logging

logger = loggin.getLogger(__name__)

class Phpbb3Group(models.Model):
    groups = models.ManyToManyField(Group)
    group_id = models.PositiveIntegerField()
    group_name = models.CharField(max_length=254)

class Phpbb3User(models.Model):
    user = models.OneToOneField(User)
    phpbb_user_id = models.PositiveIntegerField()
    phpbb_user_name = models.CharField(max_length=254)
    phpbb_groups = models.ManyToManyField(PhpbbGroup, blank=True, null=True)

class Phpbb3Service(BaseServiceModel):
    mysql_user = models.CharField(max_length=254)
    mysql_password = models.CharField(max_length=254)
    mysql_database_name = models.CharField(max_length=254)
    mysql_database_host = models.CharField(max_length=254, default='127.0.0.1')
    mysql_database_port = models.PositiveIntegerField(default=3306)

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

    SQL_REMOVE_USER_GROUP = r"DELETE FROM phpbb_user_group WHERE user_id=%s AND group_id=%s "

    SQL_GET_ALL_GROUPS = r"SELECT group_id, group_name FROM phpbb_groups"

    SQL_GET_USER_GROUPS = r"SELECT phpbb_groups.group_name FROM phpbb_groups , phpbb_user_group WHERE " \
                          r"phpbb_user_group.group_id = phpbb_groups.group_id AND user_id=%s"

    SQL_ADD_USER_AVATAR = r"UPDATE phpbb_users SET user_avatar_type=2, user_avatar_width=64, user_avatar_height=64, user_avatar=%s WHERE user_id = %s"
    
    SQL_CLEAR_USER_PERMISSIONS = r"UPDATE phpbb_users SET user_permissions = '' WHERE user_Id = %s"    


    def __get_cursor(self):
        db = MySQLdb.connect(user=self.mysql_user, passwd=self.mysql_password, db=self.mysql_database_name, host=self.mysql_database_host, port=self.mysql_database_port)
        return db.cursor()
        
    def __add_avatar(self, user_id, character_id):
        logger.debug("Adding EVE character id %s portrait as phpbb avater for user %s" % (character_id, user_id))
        avatar_url = "http://image.eveonline.com/Character/" + character_id + "_64.jpg"
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_ADD_USER_AVATAR, [avatar_url, user_id])

    def __gen_hash(self, password):
        return phpbb3_context.encrypt(password)

    def __santatize_username(self, username):
        return re.sub(r'[^\w+]+', '_', username) 

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
            logger.error("Groupname %s not found on phpbb. Unable to determine group id." % group_name)
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

    def __add_user_to_group(user_id, group_id):
        logger.debug("Adding phpbb3 user id %s to group id %s" % (user_id, group_id))
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_ADD_USER_GROUP, [group_id, user_id, 0])
        cursor.execute(self.SQL_CLEAR_USER_PERMISSIONS, [user_id])
        logger.info("Added phpbb user id %s to group id %s" % (user_id, group_id))

    def __remove_user_from_group(user_id, group_id):
        logger.debug("Removing phpbb3 user id %s from group id %s" % (user_id, group_id))
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_REMOVE_USER_GROUP, [user_id, group_id])
        cursor.execute(self.SQL_CLEAR_USER_PERMISSIONS, [user_id])
        logger.info("Removed phpbb user id %s from group id %s" % (user_id, group_id))

    def __update_user_info(username, email=None, password):
        logger.debug("Updating phpbb user %s info: username %s password of length %s" % (username, email, len(password)))
        pwhash = self..__gen_hash(password)
        cursor = self.__get_cursor()
        cursor.execute(self.SQL_DIS_USER, [email, pwhash, username])
        logger.info("Updated phpbb user %s info" % username)

    def __add_user(username, email=None, password):
        logger.debug("Adding phpbb user with username %s" % username)
        cursor = self.__get_cursor()
        pwhash = self.__gen_hash(password)
        cursor.execute(self..SQL_ADD_USER, [username, username, pwhash,
                                                            email, 2, self.__get_current_utc_date(),
                                                            "", ""])
        logger.info("Added phpbb user %s" % username)

    def test_connection(self):
        try:
            self.__get_cursot()
            return True
        except:
            return False

    
    
