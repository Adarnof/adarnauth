from django.apps import AppConfig


class GroupmanagementConfig(AppConfig):
    name = 'groupmanagement'

    def ready(self):
        import groupmanagement.signals
