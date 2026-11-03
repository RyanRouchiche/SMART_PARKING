import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from parking.models import ParkingMembership


def presence_groups(user):
    rows = list(ParkingMembership.objects.filter(user=user).values_list('parking_id', 'role'))
    watch = [f'presence_{p}' for p, role in rows if role == ParkingMembership.OWNER]
    notify = [f'presence_{p}' for p, _ in rows]
    return watch, notify


class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.watch, self.notify = [], []
        if not self.user.is_authenticated:
            return await self.close()
        self.watch, self.notify = await database_sync_to_async(presence_groups)(self.user)
        for group in self.watch:
            await self.channel_layer.group_add(group, self.channel_name)
        await self.accept()
        await self.update_user_status("Online")

    async def disconnect(self, close_code):
        for group in self.watch:
            await self.channel_layer.group_discard(group, self.channel_name)
        if self.user.is_authenticated:
            await self.update_user_status("Offline")

    async def update_user_status(self, status):
        for group in self.notify:
            await self.channel_layer.group_send(
                group,
                {'type': 'send_user_status', 'id': str(self.user.id), 'status': status},
            )

    async def send_user_status(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['id'],
            'status': event['status']
        }))
