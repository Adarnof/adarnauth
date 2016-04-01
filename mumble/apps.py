from __future__ import unicode_literals

from django.apps import AppConfig


class MumbleConfig(AppConfig):
    name = 'mumble'

    def ready(self):
        import mumble.tasks
