import json
from channels.generic.websocket import AsyncWebsocketConsumer


class UserStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            await self.channel_layer.group_add('online_users', self.channel_name)
            await self.accept()
            await self.update_user_status("Online")

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard('online_users', self.channel_name)
            await self.update_user_status("Offline")

    async def update_user_status(self, status):
        await self.channel_layer.group_send(
            'online_users',
            {
                'type': 'send_user_status',
                'id': str(self.user.id),
                'status': status
            }
        )

    async def send_user_status(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['id'],
            'status': event['status']
        }))
