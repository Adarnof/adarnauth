from django.apps import AppConfig


class EveonlineConfig(AppConfig):
    name = 'eveonline'

    def ready(self):
        import eveonline.signals
        import eveonline.tasks
