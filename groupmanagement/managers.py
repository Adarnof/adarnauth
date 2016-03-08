from django.db import models

class GroupApplicationManager(models.Manager):
    def get_accepted(self):
        return super(GroupApplicationManager, self).get_queryset().filter(response=True)

    def get_rejected(self):
        return super(GroupApplicationManager, self).get_queryset().filter(response=False)

    def get_open(self):
        return super(GroupApplicationManager, self).get_queryset().filter(response=None)

class ExtendedGroupManager(models.Manager):
    def get_parents_for_user(self, user):
        parents = []
        for g in self.model.objects.all():
            if g.owner == user or user in g.admins.all():
                parents.append(g)
        return parents


