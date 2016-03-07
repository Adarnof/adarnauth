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
    email = models.EmailField(max_length=255, null=True, blank=True, unique=True)
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
        else:
            return None

    def get_short_name(self):
        return str(self.main_character_id)
    def get_full_name(self):
        return str(self)

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
    url = models.CharField(max_length=254)
    session = models.OneToOneField(Session, on_delete=models.CASCADE)
    action = models.CharField(max_length=6, default='login')

    def __generate_hash(self, request, salt=None):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        if not salt:
            salt = uuid.uuid4().hex
        hash = hashlib.sha512(request.session.session_key + salt).hexdigest()
        return salt, hash

    def populate(self, request):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        salt, hash = self.__generate_hash(request)
        self.salt = salt
        self.hash = hash
        self.session = Session.objects.get(session_key=request.session.session_key)
        if 'next' in request.GET:
            self.url = resolve(request.GET['next']).url_name
        else:
            self.url='auth_profile'

    def validate(self, request):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        salt, hash = self.__generate_hash(request, salt=self.salt)
        if 'state' in request.GET:
            if hash == request.GET['state']:
                return True
        return False

    def exchange(self, request):
        if not request.session.exists(request.session.session_key):
            request.session.create()
        if self.validate(request):
            self.delete()
            return self.url
        else:
            self.delete()
            return None
