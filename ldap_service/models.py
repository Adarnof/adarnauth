from __future__ import unicode_literals
from django.db import models
import ldap
import logging

logger = logging.getLogger(__name__)

class LdapService(models.Model):
    uri = models.CharField(max_length=254)
    dn = models.CharField(max_length=254, blank=True)
    password = models.CharField(max_length=254, blank=True)
    base = models.CharField(max_length=254)
    
    USER_OU = "ou=People"
    GROUP_OU = "ou=Groups"

    def __init__(self, *args, **kwargs):
        super(LdapServer, self).__init__(*args, **kwargs)
        try:
            self.server = self.__get_server
        except:
            self.server = None

    def __del__(self, *args, **kwargs):
        if self.server:
            self.server.unbind()

    def __get_server(self):
        server = ldap.initialize(uri=uri)
        server.simple_bind(who=self.dn, cred=self.password)

    def __add_dn(self, dn, attrs=None):
        self.server.add(dn, attrs)

    def __del_dn(self, dn):
        self.server.delete(dn)

    def __set_pw(self, dn, pw):
        self.server.passwd(dn, pw)

    def __rn_dn(self, dn, newrdn):
        self.server.rename(dn, newrdn)

    def __compare(self, dn, attr, value):
        out = self.server.compare(dn, attr, value)
        if out:
            return True
        return False

    def __mod(self, dn, **kwargs):
        modlist = ldap.modlist.addModlist(kwargs)
        self.server.modify(dn, modlist)

    def __gen_group_dn(self, groupname):
        return "cn=%s,%s,%s" % (groupname, self.GROUP_OU, self.base)

    def __gen_user_dn(self, username):
        return "uid=%s,%s,%s" % (username, self.USER_OU, self.base)

    def __gen_user_uid(self, dn):
        return str.split(dn, str=',')[0]

    def _add_user(self, username, password):
        dn = self.__gen_user_dn(username)
        attrs["objectClass"] = ['top', 'account', 'simpleSecurityObject']
        #plaintext, need to fix
        attrs["userPassword"] = password
        self.__add_dn(dn, attrs)

    def _add_group(self, groupname):
        dn = self.__gen_group_dn(groupname)
        attrs["objectClass"] = ["groupofnames"]
        attrs["member"] = ["uid=%s" % self.__gen_admin_uid(self.dn)]
        self.__add_dn(dn, attrs)

    def _del_group(self, groupname):
        dn = self.__gen_group_dn(groupname)
        self.__del_dn(dn)

    def _del_user(self, username):
        dn = self.__gen_user_dn(username)
        self.__del_dn(dn)

    def _set_pw(self, username, password):
        dn = self.__gen_user_dn(username)
        self.__set_pw(username, password)

    def _add_group_members(self, groupname, usernames):
        group_dn = self.__gen_group_dn(groupname)
        for username in usernames:
            uid = "uid=%s" % username
            dn = "%s,%s" % (uid, group_dn)
            self.__add_dn(dn)

    def _del_group_members(self, groupname, usernames):
        group_dn = self.__gen_group_dn(groupname)
        if self.__gen_user_uid(self.dn) in usernames:
            #protect against removing admin account so it doesn't break
            usernames.remove(self.__gen_user_uid(self.dn))
        for username in usernames:
            uid = "uid=%s" % username
            dn = "%s,%s" % (uid, group_dn)
            self.__del_dn(dn)

    def test_connection(self):
        try:
            obj = self.__get_server
            return True
        except:
            return False
