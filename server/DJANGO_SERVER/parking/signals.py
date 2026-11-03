from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from users.models import User
from .models import ParkingMembership


def access_group(user_id, parking_id):
    return f"access_{user_id}_{parking_id}"


def revoke_access(user_id, parking_ids):
    groups = [access_group(user_id, p) for p in parking_ids]

    def send():
        layer = get_channel_layer()
        for group in groups:
            async_to_sync(layer.group_send)(group, {'type': 'access.revoked'})

    transaction.on_commit(send)


@receiver(post_delete, sender=ParkingMembership)
def membership_removed(sender, instance, **kwargs):
    revoke_access(instance.user_id, [instance.parking_id])


@receiver(post_save, sender=User)
def user_deactivated(sender, instance, created, **kwargs):
    if not created and not instance.is_active:
        revoke_access(instance.pk, list(instance.memberships.values_list('parking_id', flat=True)))
