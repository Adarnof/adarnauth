from django.db import models

class GroupApplicationManager(models.Manager):
    def get_accepted(self):
        return super(GroupApplicationManager, self).get_queryset().filter(response=True)

    def get_rejected(self):
        return super(GroupApplicationManager, self).get_queryset().filter(response=False)

    def get_open(self):
        return super(GroupApplicationManager, self).get_queryset().filter(response=None)
