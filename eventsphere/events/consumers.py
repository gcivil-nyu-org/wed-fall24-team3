# events/consumers.py

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import ChatRoom, ChatMessage, RoomMember, Notification


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.room_group_name = f"chat_{self.room_id}"

        chat_room = await self.get_chat_room(self.room_id)
        if not chat_room:
            await self.close()
            return

        user_id = self.scope["user"].id
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
        message = data.get("message")
        user = self.scope["user"]
        if message:
            await self.save_message(message, user)
            chat_room = await self.get_chat_room(self.room_id)
            await notify_group_members(chat_room, user, message, "chat_message")
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "username": user.username,
                    "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(
                {
                    "message": event["message"],
                    "username": event["username"],
                    "timestamp": event["timestamp"],
                }
            )
        )

    async def user_kicked(self, event):
        """Handle user kick event"""
        if event["user_id"] == self.scope["user"].id:
            # Notify the user that they are kicked and redirect them
            await self.send(text_data=json.dumps({"type": "user_kicked"}))
            await self.close()

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


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        self.group_name = f"notifications_{self.user.id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps(event["data"]))


async def notify_group_members(room, sender, message, msg_type):
    channel_layer = get_channel_layer()
    members = await get_all_members_except_sender(room, sender)
    event_name = await get_event_name(room)

    for member in members:
        title_val = "New Message" if msg_type == "chat_message" else "New Announcement"
        notif_id = await save_notification(room, member, message, title_val, event_name)
        await channel_layer.group_send(
            f"notifications_{member.user.id}",
            {
                "type": "send_notification",
                "data": {
                    "title": title_val,
                    "sub_title": event_name,
                    "message": message,
                    "timestamp": timezone.now().isoformat(),
                    "id": notif_id,
                    "msg_type": msg_type,
                },
            },
        )


@database_sync_to_async
def save_notification(room, member, message, title, sub_title):
    notif = Notification.objects.create(
        user=member.user, message=message, title=title, sub_title=sub_title
    )
    return notif.id


@database_sync_to_async
def get_all_members_except_sender(chat_room, sender):
    return list(RoomMember.objects.filter(room=chat_room).exclude(user=sender))


@database_sync_to_async
def get_event_name(room):
    return room.event.name
