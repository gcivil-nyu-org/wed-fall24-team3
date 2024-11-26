import unittest
from datetime import datetime, timezone

from events.consumers import NotificationConsumer, notify_group_members

from channels.testing import WebsocketCommunicator
from django.test import TestCase
from unittest.mock import MagicMock, AsyncMock, patch


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

        fixed_time = datetime(2024, 4, 1, 12, 0, tzinfo=timezone.utc)  # Corrected line
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
