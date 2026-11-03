from django.db.models.signals import post_save
from django.dispatch import Signal, receiver

from .models import User

user_deactivated = Signal()


@receiver(post_save, sender=User)
def announce_deactivation(sender, instance, created, **kwargs):
    if not created and not instance.is_active:
        user_deactivated.send(sender=User, user_id=instance.pk)
