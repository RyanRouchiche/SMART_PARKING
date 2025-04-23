import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import User

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

    async def receive(self, text_data):
        data = json.loads(text_data)
        print("Received from WebSocket:", data)

    async def update_user_status(self, status):
        user = await self.get_user()
        if user:
            await self.channel_layer.group_send(
                'online_users',
                {
                    'type': 'send_user_status',
                    'id': str(self.user.id),
                    'status': status
                }
            )

    @database_sync_to_async
    def get_user(self):
        try:
            return User.objects.get(id=self.user.id)
        except User.DoesNotExist:
            return None

    async def send_user_status(self, event):
        await self.send(text_data=json.dumps({
            'user_id': event['id'],
            'status': event['status']
        }))
