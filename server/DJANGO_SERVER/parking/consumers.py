import json
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from detection.events import zone_group
from .access import zone_stream, still_member


class VideoFeedConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group = None
        area = int(self.scope['url_route']['kwargs']['area'])
        parking_id = parse_qs(self.scope.get('query_string', b'').decode()).get('parking', [None])[0]
        self.parking_pk = await database_sync_to_async(zone_stream)(self.scope['user'], area, parking_id)
        await self.accept()
        if self.parking_pk is None:
            return await self.close()
        self.group = zone_group(self.parking_pk, area)
        await self.channel_layer.group_add(self.group, self.channel_name)

    async def disconnect(self, close_code):
        if self.group:
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def zone_occupancy(self, event):
        if not await database_sync_to_async(still_member)(self.scope['user'].pk, self.parking_pk):
            await self.channel_layer.group_discard(self.group, self.channel_name)
            self.group = None
            return await self.close()
        await self.send(text_data=json.dumps(event['message']))
