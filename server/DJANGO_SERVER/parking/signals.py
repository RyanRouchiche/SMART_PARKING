from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from users.interface import user_deactivated
from .access import access_group
from .models import ParkingMembership


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


@receiver(user_deactivated)
def account_deactivated(sender, user_id, **kwargs):
    revoke_access(user_id, list(ParkingMembership.objects.filter(user_id=user_id).values_list('parking_id', flat=True)))
