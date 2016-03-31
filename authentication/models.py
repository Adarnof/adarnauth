from __future__ import unicode_literals

from django.db import models
from django.utils.http import urlquote
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from managers import UserManager
from eveonline.models import EVECharacter
import logging
import uuid
import hashlib
from django.core.urlresolvers import resolve
from django.contrib.sessions.models import Session

logger = logging.getLogger(__name__)

# Custom user model. Created based on EVE Character supplemented with an email address.
class User(AbstractBaseUser, PermissionsMixin):
    main_character_id = models.PositiveIntegerField(primary_key=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD = 'main_character_id'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = 'user'
        verbose_name_plural = 'users'

    @property
    def main_character(self):
        if self.characters.filter(id=self.main_character_id).exists():
            return self.characters.get(id=self.main_character_id)
        elif EVECharacter.objects.filter(id=self.main_character_id).exists():
            logger.warn("User with main character ID %s has detached main character model" % self.get_full_name())
            return EVECharacter.objects.get(id=self.main_character_id)
        else:
            return None

    def get_full_name(self):
        return str(self.main_character_id)
    def get_short_name(self):
        if self.main_character:
            return str(self.main_character)
        else:
            return self.get_full_name()

    def __unicode__(self):
        if self.main_character:
            return str(self.main_character).encode('utf-8')
        else:
            logger.debug("Missing character model for user with main character id %s, returning id as __unicode__." % self.main_character_id)
            return self.get_short_name().encode('utf-8')

class CallbackRedirect(models.Model):
    ACTION_CHOICES = (
        ('login', 'Login'),
        ('verify', 'Verify API'),
        ('merge', 'Merge Accounts'),
    )

    salt = models.CharField(max_length=32)
    hash = models.CharField(max_length=128)
    url = models.CharField(max_length=254)
    action = models.CharField(max_length=6, default='login', choices=ACTION_CHOICES)
    session_key = models.CharField(max_length=254)
    created = models.DateTimeField(auto_now_add=True)

    def __generate_hash(self, session_key):
        return hashlib.sha512(session_key + self.salt).hexdigest()

    def __generate_salt(self):
        return uuid.uuid4().hex

    def __generate_hash_by_request(self, request, salt):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        hash = hashlib.sha512(request.session.session_key + salt).hexdigest()
        return hash

    def populate(self, request):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        salt = self.__generate_salt()
        self.salt = salt
        self.hash = self.__generate_hash(request.session.session_key)
        self.url = request.GET.get('next', '/')
        self.session_key = request.session.session_key

    def validate(self, request):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        req_hash = self.__generate_hash_by_request(request, self.salt)
        state = request.GET.get('state', None)
        if req_hash == request.GET['state']:
            if self.hash == req_hash:
                return True
        return False

    def exchange(self, request):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        if self.validate(request):
            return self.url
        else:
            return None
