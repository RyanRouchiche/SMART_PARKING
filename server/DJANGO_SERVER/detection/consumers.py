import json
import time
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from camera.interface import has_camera
from parking.interface import access_group, is_member, stream_parking
from . import state
from .events import zone_group

RECHECK_INTERVAL = 60


def stream_access(user, area, parking_id):
    parking_pk = stream_parking(user, area, parking_id)
    return parking_pk if parking_pk is not None and has_camera(parking_pk, area) else None


class VideoFeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.groups_joined = []
        self.user_id = self.scope['user'].pk
        area = int(self.scope['url_route']['kwargs']['area'])
        parking_id = parse_qs(self.scope.get('query_string', b'').decode()).get('parking', [None])[0]
        self.parking_pk = None
        candidate = await database_sync_to_async(stream_parking)(self.scope['user'], area, parking_id)
        if candidate is not None:
            await self.join(access_group(self.user_id, candidate))
            self.parking_pk = await database_sync_to_async(stream_access)(self.scope['user'], area, str(candidate))
        if candidate is None or self.parking_pk != candidate:
            await self.accept()
            return await self.revoke()
        self.checked_at = time.monotonic()
        await self.join(zone_group(self.parking_pk, area))
        await self.accept()
        current = await sync_to_async(state.latest)(self.parking_pk, area)
        if not state.is_stale(current):
            await self.send(text_data=json.dumps(state.public_message(current)))

    async def join(self, group):
        await self.channel_layer.group_add(group, self.channel_name)
        self.groups_joined.append(group)

    async def disconnect(self, close_code):
        for group in self.groups_joined:
            await self.channel_layer.group_discard(group, self.channel_name)
        self.groups_joined = []

    async def revoke(self):
        await self.disconnect(None)
        await self.close()

    async def zone_occupancy(self, event):
        if time.monotonic() - self.checked_at >= RECHECK_INTERVAL:
            if not await database_sync_to_async(is_member)(self.user_id, self.parking_pk):
                return await self.revoke()
            self.checked_at = time.monotonic()
        await self.send(text_data=json.dumps(event['message']))

    async def access_revoked(self, event):
        await self.revoke()
