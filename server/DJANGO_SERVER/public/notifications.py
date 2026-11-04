import logging

import firebase_admin
import redis
from django.core.cache import cache
from firebase_admin import messaging

from detection.interface import AVAILABILITY_STREAM
from parking.interface import published_parking
from .models import DriverDevice, Favorite

logger = logging.getLogger(__name__)

GROUP = 'notif-worker'
NOTIFIED_TTL = 30 * 60
MESSAGES = {
    'fr': ("Des places se libèrent", "{name} : {free} place(s) libre(s) maintenant."),
    'ar': ("أماكن شاغرة الآن", "{name}: {free} مكان شاغر الآن."),
}


class InvalidToken(Exception):
    pass


class FcmSender:
    def __init__(self):
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app()

    def send(self, token, title, body, data):
        message = messaging.Message(token=token, notification=messaging.Notification(title=title, body=body), data=data)
        try:
            messaging.send(message)
        except (messaging.UnregisteredError, messaging.SenderIdMismatchError) as e:
            raise InvalidToken() from e


def notified_key(device_id, parking_id):
    return f"notified:{device_id}:{parking_id}"


def notify_freed(parking_id, free, sender):
    parking = published_parking(parking_id)
    if parking is None:
        return 0
    users = Favorite.objects.filter(parking_id=parking_id, notify=True).values_list('user_id', flat=True)
    sent = 0
    for device in DriverDevice.objects.filter(user_id__in=users, user__is_active=True).select_related('user'):
        if not cache.add(notified_key(device.pk, parking_id), True, NOTIFIED_TTL):
            continue
        title, body = MESSAGES.get(device.user.language, MESSAGES['fr'])
        try:
            sender.send(device.token, title, body.format(name=parking['name'], free=free), {'parking_id': str(parking_id)})
            sent += 1
        except InvalidToken:
            device.delete()
        except Exception:
            logger.exception("Notification to device %s failed", device.pk)
    return sent


def ensure_group(client):
    try:
        client.xgroup_create(AVAILABILITY_STREAM, GROUP, id='$', mkstream=True)
    except redis.ResponseError as e:
        if 'BUSYGROUP' not in str(e):
            raise


def process(client, sender, consumer, block_ms=5000):
    handled = 0
    for _, messages in client.xreadgroup(GROUP, consumer, {AVAILABILITY_STREAM: '>'}, count=100, block=block_ms) or []:
        for message_id, fields in messages:
            notify_freed(fields[b'parking_id'].decode(), int(fields[b'free_after']), sender)
            client.xack(AVAILABILITY_STREAM, GROUP, message_id)
            handled += 1
    return handled
