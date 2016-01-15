from django.apps import AppConfig


class PhpbbConfig(AppConfig):
    name = 'phpbb'

    def ready(self):
        import phpbb.tasks
