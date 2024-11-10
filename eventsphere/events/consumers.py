# events/consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import ChatRoom, ChatMessage, RoomMember

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        chat_room = await self.get_chat_room(self.room_id)
        if not chat_room:
            await self.close()
            return

        user_id = self.scope['user'].id
        self.user_member = await self.get_room_member(chat_room, user_id)
        if not self.user_member or self.user_member.is_kicked:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message')
        user = self.scope['user']

        if message:
            await self.save_message(message, user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': user.username,
                    'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'timestamp': event['timestamp'],
        }))

    @database_sync_to_async
    def get_chat_room(self, room_id):
        return ChatRoom.objects.filter(id=room_id).first()

    @database_sync_to_async
    def get_room_member(self, chat_room, user_id):
        return RoomMember.objects.filter(room=chat_room, user_id=user_id).first()

    @database_sync_to_async
    def save_message(self, content, user):
        chat_room = ChatRoom.objects.get(id=self.room_id)
        ChatMessage.objects.create(room=chat_room, user=user, content=content)
