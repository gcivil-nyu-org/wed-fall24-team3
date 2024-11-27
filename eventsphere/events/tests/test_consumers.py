import unittest
import datetime as dt
from unittest.mock import AsyncMock, MagicMock, patch

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import User
from django.test import TestCase

from events.consumers import ChatConsumer
from events.consumers import NotificationConsumer, notify_group_members, json

from events.models import ChatRoom, RoomMember


class ChatConsumerTestCase(unittest.IsolatedAsyncioTestCase):
    """Unit tests for the ChatConsumer."""

    def setUp(self):
        """Set up test variables."""
        self.room_id = 123
        self.group_name = f"chat_{self.room_id}"
        self.user = MagicMock(spec=User)
        self.user.id = 1
        self.user.username = "testuser"
        self.user.is_authenticated = True
        self.url_route = {"kwargs": {"room_id": self.room_id}}

    @patch("events.consumers.ChatConsumer.get_chat_room", new_callable=AsyncMock)
    async def test_unauthenticated_connection(self, mock_get_chat_room):
        """Test that unauthenticated users cannot connect."""
        unauthenticated_user = MagicMock(spec=User)
        unauthenticated_user.is_authenticated = False

        communicator = WebsocketCommunicator(
            application=ChatConsumer.as_asgi(),
            path=f"/ws/chat/{self.room_id}/",
        )

        mock_get_chat_room.return_value = None
        communicator.scope["user"] = unauthenticated_user
        communicator.scope["url_route"] = self.url_route

        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    @patch("channels.layers.get_channel_layer", new_callable=MagicMock)
    @patch("events.consumers.ChatConsumer.get_chat_room", new_callable=AsyncMock)
    @patch("events.consumers.ChatConsumer.get_room_member", new_callable=AsyncMock)
    async def test_authenticated_connection(
        self, mock_get_room_member, mock_get_chat_room, mock_get_channel_layer
    ):
        """
        Test that authenticated users can connect and are added to the correct group
        when the chat room exists and the user is a valid member.
        """
        # Mock the chat room exists
        mock_chat_room = MagicMock(spec=ChatRoom)
        mock_get_chat_room.return_value = mock_chat_room

        # Mock user is a member and not kicked
        mock_room_member = MagicMock(spec=RoomMember)
        mock_room_member.is_kicked = False
        mock_get_room_member.return_value = mock_room_member

        # Create a mock channel_layer with group_add as AsyncMock
        mock_channel_layer = MagicMock()
        mock_channel_layer.group_add = AsyncMock()
        mock_channel_layer.group_discard = AsyncMock()
        mock_channel_layer.group_send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        communicator = WebsocketCommunicator(
            application=ChatConsumer.as_asgi(),
            path=f"/ws/chat/{self.room_id}/",
        )
        communicator.scope["user"] = self.user
        communicator.scope["url_route"] = self.url_route

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()

    @patch("channels.layers.get_channel_layer", new_callable=MagicMock)
    @patch("events.consumers.ChatConsumer.get_chat_room", new_callable=AsyncMock)
    @patch("events.consumers.ChatConsumer.get_room_member", new_callable=AsyncMock)
    @patch("events.consumers.ChatConsumer.save_message", new_callable=AsyncMock)
    @patch("events.consumers.get_all_members_except_sender", new_callable=AsyncMock)
    @patch("django.utils.timezone.now")
    async def test_chat_message(
        self,
        mock_now,
        mock_get_all_members_except_sender,
        mock_save_message,
        mock_get_room_member,
        mock_get_chat_room,
        mock_get_channel_layer,
    ):
        """Test that chat_message event sends the correct data to the WebSocket."""
        event = {
            "message": "Hello from group!",
            "username": self.user.username,
            "timestamp": "2024-04-01 12:00:00",
        }

        # Create a mock channel_layer with send as AsyncMock
        mock_channel_layer = MagicMock()
        mock_channel_layer.send = AsyncMock()
        mock_get_channel_layer.return_value = mock_channel_layer

        mock_chat_room = MagicMock(spec=ChatRoom)
        mock_get_chat_room.return_value = mock_chat_room

        mock_room_member = MagicMock(spec=RoomMember)
        mock_room_member.is_kicked = False
        mock_get_room_member.return_value = mock_room_member

        mock_member_1 = MagicMock(spec=RoomMember)
        mock_member_1.is_kicked = False
        mock_member_2 = MagicMock(spec=RoomMember)
        mock_member_2.is_kicked = False

        fixed_time = dt.datetime(
            2024, 4, 1, 12, 0, tzinfo=dt.timezone.utc
        )  # Corrected line
        mock_now.return_value = fixed_time

        mock_get_all_members_except_sender.return_values = [
            mock_member_1,
            mock_member_2,
        ]

        mock_save_message.return_value = None

        communicator = WebsocketCommunicator(
            application=ChatConsumer.as_asgi(),
            path=f"/ws/chat/{self.room_id}/",
        )
        communicator.scope["user"] = self.user
        communicator.scope["url_route"] = self.url_route

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Simulate receiving a chat_message event by sending the event directly to the consumer
        await communicator.send_json_to(event)

        # Since the consumer handles 'chat_message' by sending data back,
        # we can try to receive the message
        response = await communicator.receive_from()
        response_data = json.loads(response)
        self.assertEqual(response_data, event)

        await communicator.disconnect()


class NotificationConsumerTestCase(TestCase):

    def setUp(self):
        # Create a mock user
        self.user = MagicMock()
        self.user.id = 1
        self.user.is_authenticated = True
        self.group_name = f"notifications_{self.user.id}"
        self.channel_name = "sample_channel"

    async def test_unauthenticated_connection(self):
        """Test that unauthenticated users cannot connect"""
        unauthenticated_user = MagicMock()
        unauthenticated_user.is_authenticated = False

        communicator = WebsocketCommunicator(
            application=NotificationConsumer.as_asgi(),
            path="/ws/notifications/",
        )
        communicator.scope["user"] = unauthenticated_user

        connected, _ = await communicator.connect()
        self.assertFalse(connected)

    async def test_authenticated_connection(self):
        """Test that authenticated users can connect and are added to the correct group"""
        communicator = WebsocketCommunicator(
            application=NotificationConsumer.as_asgi(),
            path="/ws/notifications/",
        )
        communicator.scope["user"] = self.user

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()


class NotifyGroupMembersTestCase(unittest.IsolatedAsyncioTestCase):
    @patch("events.consumers.get_channel_layer")
    @patch("events.consumers.get_all_members_except_sender")
    @patch("events.consumers.get_event_name")
    @patch("events.consumers.save_notification")
    @patch("django.utils.timezone.now")
    async def test_notify_group_members(
        self,
        mock_now,
        mock_save_notification,
        mock_get_event_name,
        mock_get_all_members_except_sender,
        mock_get_channel_layer,
    ):
        """
        Test the notify_group_members function to ensure it correctly sends notifications
        to all group members except the sender. All external dependencies are mocked.
        """

        mock_room = MagicMock()
        mock_room.id = 1

        mock_sender = MagicMock()
        mock_sender.user = MagicMock()
        mock_sender.user.id = 999

        message = "Hello, this is a test message!"
        msg_type = "chat_message"

        mock_members = [
            MagicMock(user=MagicMock(id=1)),
            MagicMock(user=MagicMock(id=2)),
            MagicMock(user=MagicMock(id=3)),
        ]
        mock_get_all_members_except_sender.return_value = mock_members

        mock_event_name = "Test Event"
        mock_get_event_name.return_value = mock_event_name
        mock_notif_url_path = "1"

        mock_save_notification.side_effect = [101, 102, 103]

        fixed_time = dt.datetime(
            2024, 4, 1, 12, 0, tzinfo=dt.timezone.utc
        )  # Corrected line
        mock_now.return_value = fixed_time

        mock_group_send = AsyncMock()
        mock_channel_layer = AsyncMock()
        mock_channel_layer.group_send = mock_group_send
        mock_get_channel_layer.return_value = mock_channel_layer

        await notify_group_members(mock_room, mock_sender, message, msg_type)

        mock_get_all_members_except_sender.assert_awaited_once_with(
            mock_room, mock_sender
        )

        mock_get_event_name.assert_awaited_once_with(mock_room)

        expected_title = (
            "New Message" if msg_type == "chat_message" else "New Announcement"
        )
        for member, notif_id in zip(mock_members, [101, 102, 103]):
            mock_save_notification.assert_any_await(
                mock_room,
                member,
                message,
                expected_title,
                mock_event_name,
                mock_notif_url_path,
            )

        self.assertEqual(mock_save_notification.await_count, len(mock_members))

        for member, notif_id in zip(mock_members, [101, 102, 103]):
            mock_group_send.assert_any_await(
                f"notifications_{member.user.id}",
                {
                    "type": "send_notification",
                    "data": {
                        "title": expected_title,
                        "sub_title": mock_event_name,
                        "message": message,
                        "timestamp": fixed_time.isoformat(),
                        "id": notif_id,
                        "msg_type": msg_type,
                        "url_link": mock_notif_url_path,
                    },
                },
            )

        self.assertEqual(mock_group_send.await_count, len(mock_members))

        mock_get_channel_layer.assert_called_once()
