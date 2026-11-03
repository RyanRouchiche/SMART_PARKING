import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from detection.events import zone_group
from .access import zone_stream
from .signals import access_group


class VideoFeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.groups_joined = []
        area = int(self.scope['url_route']['kwargs']['area'])
        parking_id = parse_qs(self.scope.get('query_string', b'').decode()).get('parking', [None])[0]
        parking_pk = await database_sync_to_async(zone_stream)(self.scope['user'], area, parking_id)
        await self.accept()
        if parking_pk is None:
            return await self.close()
        self.groups_joined = [zone_group(parking_pk, area), access_group(self.scope['user'].pk, parking_pk)]
        for group in self.groups_joined:
            await self.channel_layer.group_add(group, self.channel_name)

    async def disconnect(self, close_code):
        for group in self.groups_joined:
            await self.channel_layer.group_discard(group, self.channel_name)
        self.groups_joined = []

    async def zone_occupancy(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def access_revoked(self, event):
        await self.disconnect(None)
        await self.close()
