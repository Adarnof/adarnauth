from django.dispatch import Signal

user_loses_access = Signal(providing_args=['user'])
user_gains_access = Signal(providing_args=['user'])
