import json
from datetime import timedelta
from unittest.mock import patch, MagicMock, ANY

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now

from events.forms import (
    CreatorProfileForm,
    UserProfileForm,
    EventForm,
    TicketPurchaseForm,
)
from events.models import (
    Event,
    AdminProfile,
    CreatorProfile,
    UserProfile,
    ChatRoom,
    RoomMember,
    Ticket,
    Notification,
)
from events.views import fetch_unread_notif_db


# from better_profanity import profanity


class NotificationTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(username="testuser", password="testpass")

        self.notification_id = 1

    @patch("events.views.fetch_unread_notif_db")
    def test_view_notifications_authenticated(self, mock_fetch_unread_notif_db):
        """
        Test that the view_notifications view successfully fetches unread notifications
        and renders the correct template with the expected context.
        """

        mock_unread_notifications = [
            {
                "id": 1,
                "message": "Test Notification",
                "created_at": "2024-01-01T00:00:00Z",
                "type": "info",
                "title": "Test Title",
                "sub_title": "Test Sub-title",
                "url_link": "2",
            }
        ]
        mock_fetch_unread_notif_db.return_value = mock_unread_notifications

        login = self.client.login(username="testuser", password="testpass")
        self.assertTrue(login, "User failed to log in.")

        response = self.client.get(reverse("notifications"))

        mock_fetch_unread_notif_db.assert_called_once_with(self.user)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/notifications.html")
        self.assertIn("notifications", response.context)
        self.assertEqual(response.context["notifications"], mock_unread_notifications)

    def test_view_notifications_unauthenticated(self):
        """
        Test that unauthenticated users are redirected to the login page when accessing view_notifications.
        """
        response = self.client.get(reverse("notifications"))

        self.assertEqual(response.status_code, 302)
        login_url = reverse("login")
        notifications_url = reverse("notifications")
        self.assertRedirects(response, f"{login_url}?next={notifications_url}")

    @patch("events.views.fetch_unread_notif_db")
    def test_get_user_unread_notifications_authenticated(
        self, mock_fetch_unread_notif_db
    ):
        """
        Test that the get_user_unread_notifications view returns the correct JSON response
        with unread notifications.
        """
        mock_unread_notifications = [
            {
                "id": 1,
                "message": "Test Notification",
                "created_at": "2024-01-01T00:00:00Z",
                "type": "info",
                "title": "Test Title",
                "sub_title": "Test Sub-title",
                "url_link": "/test-url/",
            }
        ]
        mock_fetch_unread_notif_db.return_value = mock_unread_notifications

        login = self.client.login(username="testuser", password="testpass")
        self.assertTrue(login, "User failed to log in.")

        response = self.client.get(reverse("get_user_unread_notifications"))

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, mock_unread_notifications)

    @patch("events.models.Notification.objects.filter")
    def test_fetch_unread_notif_db(self, mock_filter):
        """
        Test the fetch_unread_notif_db helper function to ensure it correctly queries the database
        and returns the expected data.
        """
        mock_queryset = MagicMock()
        mock_filter.return_value.order_by.return_value = mock_queryset
        mock_queryset.values.return_value = [
            {
                "id": 1,
                "message": "Test Notification",
                "created_at": "2024-01-01T00:00:00Z",
                "type": "info",
                "title": "Test Title",
                "sub_title": "Test Sub-title",
                "url_link": "/test-url/",
            },
            {
                "id": 2,
                "message": "Another Notification",
                "created_at": "2024-01-02T00:00:00Z",
                "type": "warning",
                "title": "Another Title",
                "sub_title": "Another Sub-title",
                "url_link": "/another-url/",
            },
        ]

        result = fetch_unread_notif_db(self.user)

        mock_filter.assert_called_once_with(user=self.user, is_read=False)
        mock_filter.return_value.order_by.assert_called_once_with("-created_at")
        mock_queryset.values.assert_called_once_with(
            "id", "message", "created_at", "type", "title", "sub_title", "url_link"
        )
        self.assertEqual(result, mock_queryset.values.return_value)

    @patch("events.models.Notification.objects.get")
    def test_mark_as_read_success(self, mock_get):
        """
        Test that the mark_as_read view successfully marks a notification as read.
        """
        mock_notification = MagicMock(spec=Notification)
        mock_get.return_value = mock_notification

        login = self.client.login(username="testuser", password="testpass")
        self.assertTrue(login, "User failed to log in.")

        response = self.client.post(
            reverse("mark_as_read", args=[self.notification_id])
        )

        mock_get.assert_called_once_with(id=self.notification_id, user=self.user)
        mock_notification.save.assert_called_once()
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {"success": True, "message": "Notification marked as read."},
        )

    @patch("events.models.Notification.objects.get")
    def test_mark_as_read_notification_not_found(self, mock_get):
        """
        Test that the mark_as_read view returns a 404 response when the notification does not exist.
        """
        mock_get.side_effect = Notification.DoesNotExist

        login = self.client.login(username="testuser", password="testpass")
        self.assertTrue(login, "User failed to log in.")

        response = self.client.post(
            reverse("mark_as_read", args=[self.notification_id])
        )

        mock_get.assert_called_once_with(id=self.notification_id, user=self.user)
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            response.content, {"success": False, "message": "Notification not found."}
        )

    @patch("events.models.Notification.objects.filter")
    def test_mark_all_as_read_success(self, mock_filter):
        """
        Test that the mark_all_as_read view successfully marks all unread notifications as read.
        """
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset

        login = self.client.login(username="testuser", password="testpass")
        self.assertTrue(login, "User failed to log in.")

        response = self.client.post(reverse("mark_all_as_read"))

        mock_filter.assert_called_once_with(user=self.user, is_read=False)
        mock_queryset.update.assert_called_once_with(is_read=True)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})


class DeleteEventViewTest(TestCase):
    def setUp(self):
        # Set up a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)

        # Set up a creator
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.profile = CreatorProfile.objects.create(creator=self.creator_user)

        # Set up a Admin
        self.superuser = User.objects.create_superuser(
            username="superuser", password="superpass"
        )

        self.client = Client()

    @patch("events.views.get_object_or_404")
    def test_delete_event_as_regular_user_post(self, mock_get_object):
        mock_event = MagicMock()
        mock_get_object.return_value = mock_event

        # Login as an User
        self.client.login(username="testuser", password="testpass")

        response = self.client.post(
            reverse("delete_event", args=[1])
        )  # Event ID is mocked

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    @patch("events.views.get_object_or_404")
    def test_delete_event_as_superuser_post(self, mock_get_object):
        mock_event = MagicMock()
        mock_get_object.return_value = mock_event

        # login as an Admin
        self.client.login(username="superuser", password="superpass")

        response = self.client.post(reverse("delete_event", args=[1]))

        mock_event.delete.assert_called_once()

        self.assertRedirects(response, reverse("event_list"))

    @patch("events.views.get_object_or_404")
    def test_get_request_renders_delete_confirmation_as_creator(self, mock_get_object):
        mock_event = MagicMock()
        mock_get_object.return_value = mock_event

        # Login as a creator
        self.client.login(username="creator", password="creatorpass")

        response = self.client.get(reverse("delete_event", args=[1]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/delete.html")
        self.assertIn("event", response.context)

    def test_anonymous_user_redirected_to_login(self):
        response = self.client.get(reverse("delete_event", args=[1]))

        self.assertRedirects(response, "/events/login/?next=/events/delete/1/")


class CreatorProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = CreatorProfile.objects.create(creator=self.user)

        self.client = Client()
        self.client.login(username="testuser", password="testpass")

    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    def test_get_request_renders_form(self, mock_ticket_filter, mock_get_or_create):
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        mock_ticket_filter.return_value = []

        response = self.client.get(reverse("creator_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], CreatorProfileForm)
        self.assertTemplateUsed(response, "events/creator_profile.html")

        mock_ticket_filter.assert_called_once_with(user=self.user)

    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.CreatorProfileForm")
    def test_post_request_valid_form(
        self, mock_form_class, mock_ticket_filter, mock_get_or_create
    ):
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        mock_ticket_filter.return_value = []

        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form

        response = self.client.post(reverse("creator_profile"), data={"field": "value"})

        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse("creator_profile"))

    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.CreatorProfileForm")
    def test_post_request_invalid_form(
        self, mock_form_class, mock_ticket_filter, mock_get_or_create
    ):
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        mock_ticket_filter.return_value = []

        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form_class.return_value = mock_form

        response = self.client.post(
            reverse("creator_profile"), data={"field": "invalid_value"}
        )

        mock_form.save.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/creator_profile.html")

    def test_creator_profile_as_admin(self):
        self.client.logout()
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.client.login(username="admin", password="adminpass")

        response = self.client.get(reverse("creator_profile"))

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_creator_profile_as_user(self):
        self.client.logout()
        self.user = User.objects.create_user(username="user", password="pass")
        self.profile = UserProfile.objects.create(user=self.user)
        self.client.login(username="user", password="pass")

        response = self.client.get(reverse("creator_profile"))

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )


class UserProfileViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)

        self.client = Client()
        self.client.login(username="testuser", password="testpass")

    def test_user_profile_as_admin(self):
        self.client.logout()
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.client.login(username="admin", password="adminpass")

        response = self.client.get(reverse("user_profile"))

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_user_profile_as_creator(self):
        self.client.logout()
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.profile = CreatorProfile.objects.create(creator=self.creator_user)
        self.client.login(username="creator", password="creatorpass")

        response = self.client.get(reverse("user_profile"))

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    @patch("events.views.UserProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    def test_get_request_renders_form_and_groups_tickets(
        self, mock_ticket_filter, mock_get_or_create
    ):
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)

        mock_ticket_filter.return_value.values.return_value.annotate.return_value = [
            {"event__name": "Event 1", "event__id": 1, "total_tickets": 3},
            {"event__name": "Event 2", "event__id": 2, "total_tickets": 5},
        ]

        response = self.client.get(reverse("user_profile"))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["form"], UserProfileForm)
        self.assertTemplateUsed(response, "events/user_profile.html")

        mock_ticket_filter.assert_called_once_with(user=self.user)
        self.assertEqual(len(response.context["events_with_tickets"]), 2)

    @patch("events.views.UserProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.UserProfileForm")
    def test_post_request_valid_form(
        self, mock_form_class, mock_ticket_filter, mock_get_or_create
    ):
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)

        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form

        response = self.client.post(reverse("user_profile"), data={"field": "value"})

        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse("user_profile"))

    @patch("events.views.UserProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.UserProfileForm")
    def test_post_request_invalid_form(
        self, mock_form_class, mock_ticket_filter, mock_get_or_create
    ):
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)

        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form_class.return_value = mock_form

        response = self.client.post(
            reverse("user_profile"), data={"field": "invalid_value"}
        )

        mock_form.save.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/user_profile.html")


class UpdateEventViewTest(TestCase):
    def setUp(self):
        # Set up a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)

        # Set up a creator
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.profile = CreatorProfile.objects.create(creator=self.creator_user)

        # Set up a Admin
        self.superuser = User.objects.create_superuser(
            username="superuser", password="superpass"
        )

        # Initialize the client for testing
        self.client = Client()

    @patch("events.views.get_object_or_404")
    @patch("events.views.EventForm")
    def test_get_request_renders_form_as_creator(
        self, mock_event_form, mock_get_object
    ):
        # Mock the event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event

        # Mock the form instance
        mock_form_instance = MagicMock()
        mock_event_form.return_value = mock_form_instance

        # Log in as a creator
        self.client.login(username="creator", password="creatorpass")

        # Send a GET request
        response = self.client.get(reverse("update_event", args=[mock_event.id]))

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/update_event.html")
        self.assertEqual(response.context["form"], mock_form_instance)

        # Ensure get_object_or_404 was called with correct arguments
        mock_get_object.assert_called_once_with(Event, id=mock_event.id)

    @patch("events.views.get_object_or_404")
    @patch("events.views.EventForm")
    def test_get_request_renders_form_as_admin(self, mock_event_form, mock_get_object):
        # Mock the event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event

        # Mock the form instance
        mock_form_instance = MagicMock()
        mock_event_form.return_value = mock_form_instance

        # Log in as a admin
        self.client.login(username="superuser", password="superpass")

        # Send a GET request
        response = self.client.get(reverse("update_event", args=[mock_event.id]))

        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/update_event.html")
        self.assertEqual(response.context["form"], mock_form_instance)

        # Ensure get_object_or_404 was called with correct arguments
        mock_get_object.assert_called_once_with(Event, id=mock_event.id)

    @patch("events.views.get_object_or_404")
    @patch("events.views.EventForm")
    def test_get_request_renders_form_user(self, mock_event_form, mock_get_object):
        # Mock the event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event

        # Mock the form instance
        mock_form_instance = MagicMock()
        mock_event_form.return_value = mock_form_instance

        # Log in as a user
        self.client.login(username="testuser", password="testpass")

        # Send a GET request
        response = self.client.get(reverse("update_event", args=[mock_event.id]))

        # Check the response
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    @patch("events.views.get_object_or_404")
    @patch("events.views.boto3.client")
    @patch("events.views.EventForm")
    def test_post_request_valid_form_no_image(
        self, mock_event_form, mock_boto_client, mock_get_object
    ):
        # Mock the event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event

        # Mock the form validation and save
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = mock_event
        mock_event_form.return_value = mock_form

        # Log in as a creator
        self.client.login(username="creator", password="creatorpass")

        # Send a POST request without an image
        response = self.client.post(
            reverse("update_event", args=[mock_event.id]),
            data={"name": "Updated Event"},
        )

        # Ensure form.save() was called and redirection to creator_dashboard
        mock_form.save.assert_called_once()
        self.assertRedirects(
            response, reverse("creator_dashboard"), target_status_code=200
        )

    @patch("events.views.get_object_or_404")
    @patch("events.views.boto3.client")
    @patch("events.views.EventForm")
    def test_post_request_valid_form_with_image(
        self, mock_event_form, mock_boto_client, mock_get_object
    ):
        # Mock event retrieval
        mock_event = MagicMock()
        mock_event.id = 1
        mock_get_object.return_value = mock_event

        # Mock the form validation and save
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = mock_event
        mock_event_form.return_value = mock_form

        # Mock the S3 client
        mock_s3 = mock_boto_client.return_value

        # Create a mock image file as an InMemoryUploadedFile
        image_mock = SimpleUploadedFile(
            name="test_image.jpg", content=b"file_content", content_type="image/jpeg"
        )

        # Log in as a superuser
        self.client.login(username="superuser", password="superpass")

        # Send a POST request with an image
        response = self.client.post(
            reverse("update_event", args=[mock_event.id]),
            data={"name": "Updated Event", "image": image_mock},
            format="multipart",
        )

        # Verify image upload to S3
        mock_s3.upload_fileobj.assert_called_once_with(
            ANY,  # Ignore the exact file type, just ensure it's passed as a file object
            "eventsphere-images",
            "events/test_image.jpg",
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        # Ensure form.save() was called and user is redirected to event_list
        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse("event_list"))

    @patch("events.views.get_object_or_404")
    @patch("events.views.EventForm")
    def test_post_request_invalid_form(self, mock_event_form, mock_get_object):
        # Mock event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event

        # Mock form validation failure
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False  # Simulate invalid form data
        mock_event_form.return_value = mock_form

        # Log in as a regular user
        self.client.login(username="creator", password="creatorpass")

        # Send a POST request with invalid data
        response = self.client.post(
            reverse("update_event", args=[mock_event.id]), data={"name": ""}
        )

        # Ensure form.save() was not called, and form is re-rendered with 400 status
        mock_form.save.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, "events/update_event.html")
        self.assertIn("errors", response.context)


class ProfileTicketsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)
        # Create an event
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time=timezone.now() + timezone.timedelta(days=1),
            schedule="Event Schedule",
            speakers="Speaker 1",
            category="Category 1",
            numTickets=100,
            ticketsSold=0,
        )
        # Create tickets for the user
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=2,
        )

    def test_profile_tickets_view_authenticated(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("profile_tickets"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/profile_tickets.html")

        # self.assertIn("events_with_tickets", response.context)

        # Verify upcoming_events context
        upcoming_events = response.context["upcoming_events"]
        self.assertEqual(len(upcoming_events), 1)
        self.assertEqual(upcoming_events[0]["event__name"], "Test Event")
        self.assertEqual(upcoming_events[0]["total_tickets"], 2)

        # Verify past_events context is empty
        past_events = response.context["past_events"]
        self.assertEqual(len(past_events), 0)

    def test_profile_tickets_view_unauthenticated(self):
        response = self.client.get(reverse("profile_tickets"))
        login_url = reverse("login") + "?next=" + reverse("profile_tickets")
        self.assertRedirects(response, login_url)

    def test_profile_tickets_as_creator(self):
        self.client.logout()
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.profile = CreatorProfile.objects.create(creator=self.creator_user)
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("profile_tickets"))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_profile_tickets_as_admin(self):
        self.client.logout()
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("profile_tickets"))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.creator_user = User.objects.create_user(
            username="creatoruser", password="creatorpass"
        )
        self.regular_user = User.objects.create_user(
            username="testuser", password="testpass"
        )
        # Create CreatorProfile for creator_user
        self.creator_profile = CreatorProfile.objects.create(creator=self.creator_user)

    def test_login_view_get(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/login.html")
        self.assertIsInstance(response.context["form"], AuthenticationForm)

    def test_login_view_post_superuser(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "admin",
                "password": "adminpass",
            },
        )
        self.assertRedirects(response, reverse("event_list"))

    def test_login_view_post_creator(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "creatoruser",
                "password": "creatorpass",
            },
        )
        self.assertRedirects(response, reverse("creator_dashboard"))

    def test_login_view_post_regular_user(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "testuser",
                "password": "testpass",
            },
        )
        self.assertRedirects(response, reverse("user_home"))

    def test_login_view_post_invalid_credentials(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "unknown",
                "password": "nopass",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/login.html")
        form = response.context["form"]
        self.assertTrue(form.errors)


class SignupTest(TestCase):
    def setUp(self):
        self.url = reverse("signup")

    def test_signup_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

    def test_signup_post_password_mismatch(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@gmail.com",
            "password": "password123",
            "confirm_password": "password456",  # Mismatched password
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Passwords do not match." in str(m.message) for m in messages)
        )

    def test_signup_post_username_exists(self):
        # Create a user to simulate an existing username
        User.objects.create_user(username="existinguser", password="password123")

        form_data = {
            "username": "existinguser",  # Username already exists
            "email": "newuser@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Username already exists." in str(m.message) for m in messages)
        )

    def test_signup_post_no_email(self):
        form_data = {
            "username": "existinguser",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Email is required." in str(m.message) for m in messages))

    def test_signup_post_invalid_email(self):
        form_data = {
            "username": "existinguser",
            "email": "abcd",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Enter a valid email address." in str(m.message) for m in messages)
        )

    def test_signup_post_email_in_use_admin(self):
        # Create a user to simulate an existing username
        user = User.objects.create_user(
            username="user", password="password123", is_superuser=True
        )
        AdminProfile.objects.create(admin=user, email="test@gmail.com")

        form_data = {
            "username": "existinguser",
            "email": "test@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("This email is already in use." in str(m.message) for m in messages)
        )

    def test_signup_post_email_in_use_creator(self):
        # Create a user to simulate an existing username
        user = User.objects.create_user(username="user", password="password123")
        CreatorProfile.objects.create(creator=user, organization_email="test@gmail.com")

        form_data = {
            "username": "existinguser",
            "email": "test@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("This email is already in use." in str(m.message) for m in messages)
        )

    def test_signup_post_email_in_use_user(self):
        # Create a user to simulate an existing username
        user = User.objects.create_user(username="user", password="password123")
        UserProfile.objects.create(user=user, email="test@gmail.com")

        form_data = {
            "username": "existinguser",
            "email": "test@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "user",
        }
        response = self.client.post(self.url, data=form_data)

        # Check response and template
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("This email is already in use." in str(m.message) for m in messages)
        )

    def test_signup_post_success(self):
        form_data = {
            "username": "newuser",
            "email": "newuser@gmail.com",
            "password": "password123",
            "confirm_password": "password123",
            "user_type": "admin",
        }
        response = self.client.post(self.url, data=form_data)

        # Check redirection to the event list page
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("event_list"))

        # Check if user was created and logged in
        user_exists = User.objects.filter(username="newuser").exists()
        self.assertTrue(user_exists)
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            User.objects.get(username="newuser").id,
        )


class SignupTests(TestCase):
    def setUp(self):
        self.signup_url = reverse("signup")

    def test_user_signup_get_request(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")

    def test_user_signup_post_valid_data(self):
        form_data = {
            "username": "testuser",
            "email": "testuser@gmail.com",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
            "user_type": "user",
        }
        response = self.client.post(self.signup_url, data=form_data)

        # Check that user was created and logged in, and redirected to profile
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("user_profile"))
        self.assertTrue(User.objects.filter(username="testuser").exists())
        self.assertEqual(
            int(self.client.session["_auth_user_id"]),
            User.objects.get(username="testuser").id,
        )

    # def test_user_signup_post_invalid_data(self):
    #     form_data = {
    #         "username": "",  # Invalid data
    #         "password1": "password123",
    #         "password2": "password123",
    #     }
    #     response = self.client.post(self.user_signup_url, data=form_data)
    #
    #     # Should return to the signup page with form errors
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "events/user_signup.html")
    #     self.assertFalse(User.objects.filter(username="").exists())
    #     self.assertTrue(response.context["form"].errors)

    def test_creator_signup_get_request(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")
        # self.assertIsInstance(response.context["form"], UserCreationForm)

    def test_creator_signup_post_valid_data(self):
        form_data = {
            "username": "creatoruser",
            "email": "newuser@gmail.com",
            "password": "creatorpassword123",
            "confirm_password": "creatorpassword123",
            "user_type": "creator",
        }
        response = self.client.post(self.signup_url, data=form_data)

        # Check that creator was created with correct permissions, logged in, and redirected
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("creator_profile"))
        creator = User.objects.get(username="creatoruser")
        self.assertTrue(creator.is_staff)
        self.assertFalse(creator.is_superuser)
        self.assertEqual(int(self.client.session["_auth_user_id"]), creator.id)

    def test_creator_signup_post_invalid_data(self):
        form_data = {
            "username": "creatoruser",
            "email": "newuser@gmail.com",
            "password": "password123",
            "confirm_password": "differentpassword123",  # Passwords don't match
            "user_type": "creator",
        }
        response = self.client.post(self.signup_url, data=form_data)

        # Should return to the signup page with form errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/signup.html")
        self.assertFalse(User.objects.filter(username="creatoruser").exists())
        messages = list(response.context["messages"])
        # for message in messages:
        #     print(str(message))
        self.assertTrue(
            any("Passwords do not match." in str(message) for message in messages)
        )


class UserHomeViewTest(TestCase):
    def test_user_home_view(self):
        response = self.client.get(reverse("user_home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/user_home.html")


class GenerateEventQRCodeTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time=timezone.now() + timezone.timedelta(days=1),
            schedule="Event Schedule",
            speakers="Speaker 1",
            category="Category 1",
            numTickets=100,
            ticketsSold=0,
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            quantity=1,
        )

    def test_generate_event_qr_code_authenticated(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("generate_event_qr", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("qr_code", response.json())

    def test_generate_event_qr_code_no_tickets(self):
        self.client.login(username="testuser", password="testpass")
        new_event = Event.objects.create(
            name="New Event",
            location="New Location",
            date_time=timezone.now() + timezone.timedelta(days=2),
            schedule="Schedule",
            speakers="Speaker 2",
            category="Category 2",
            numTickets=50,
            ticketsSold=0,
        )
        response = self.client.get(reverse("generate_event_qr", args=[new_event.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"], "No tickets found for this event.")


class UserEventListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.client.login(username="testuser", password="testpassword")
        self.event1 = Event.objects.create(
            name="Music Concert",
            location="Stadium",
            date_time=timezone.now() + timezone.timedelta(days=5),
            schedule="Evening",
            speakers="Band A",
            category="Music",
            numTickets=100,
            ticketsSold=0,
        )
        self.event2 = Event.objects.create(
            name="Tech Conference",
            location="Convention Center",
            date_time=timezone.now() + timezone.timedelta(days=10),
            schedule="Morning",
            speakers="Speaker B",
            category="Technology",
            numTickets=200,
            ticketsSold=0,
        )

    def test_user_event_list_requires_login(self):
        self.client.logout()  # Log out the user
        response = self.client.get(reverse("user_event_list"))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        self.assertIn("login", response.url)  # Check the redirect URL

    def test_user_event_list_no_query(self):
        response = self.client.get(reverse("user_event_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/user_event_list.html")
        # self.assertEqual(len(response.context["events"]), 2)
        self.assertEqual(len(response.context["past_events"]), 0)
        self.assertEqual(len(response.context["upcoming_events"]), 2)

    def test_user_event_list_with_query(self):
        response = self.client.get(reverse("user_event_list"), {"q": "Music"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["past_events"]), 0)
        self.assertEqual(len(response.context["upcoming_events"]), 1)
        self.assertEqual(response.context["upcoming_events"][0], self.event1)

    def test_user_event_list_no_matching_query(self):
        response = self.client.get(reverse("user_event_list"), {"q": "Nonexistent"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["past_events"]), 0)
        self.assertEqual(len(response.context["upcoming_events"]), 0)


class AdminEventListViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.client.login(username="admin", password="adminpass")

    def test_admin_event_list_as_admin(self):
        response = self.client.get(reverse("event_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_list.html")

    def test_admin_event_list_as_user(self):
        self.client.logout()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)

        self.client.login(username="testuser", password="testpass")

        response = self.client.get(reverse("event_list"))

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_admin_event_list_as_creator(self):
        self.client.logout()
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.profile = CreatorProfile.objects.create(creator=self.creator_user)
        self.client.login(username="creator", password="creatorpass")

        response = self.client.get(reverse("event_list"))

        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )


class EventDetailViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time=timezone.now() + timezone.timedelta(days=1),
            schedule="Event Schedule",
            speakers="Speaker 1",
            category="Category 1",
            numTickets=100,
            ticketsSold=0,
        )

    def test_event_detail_view(self):
        response = self.client.get(reverse("event_detail", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/event_detail.html")
        self.assertEqual(response.context["event"], self.event)

    def test_event_detail_view_nonexistent(self):
        response = self.client.get(reverse("event_detail", args=[999]))
        self.assertEqual(response.status_code, 404)


class UserProfileViewTest2(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)
        self.client.login(username="testuser", password="testpass")

    def test_user_profile_get(self):
        response = self.client.get(reverse("user_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/user_profile.html")
        self.assertIsInstance(response.context["form"], UserProfileForm)
        self.assertIn("events_with_tickets", response.context)

    def test_user_profile_post_valid(self):
        response = self.client.post(
            reverse("user_profile"),
            {
                "name": "Test User",
                "age": 30,
                "bio": "This is a bio",
                "location": "Test Location",
                "interests": "Music, Tech",
                "email": "test@example.com",
            },
        )
        self.assertRedirects(response, reverse("user_profile"))
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.name, "Test User")
        self.assertEqual(profile.age, 30)
        self.assertEqual(profile.bio, "This is a bio")
        self.assertEqual(profile.location, "Test Location")
        self.assertEqual(profile.interests, "Music, Tech")
        self.assertEqual(profile.email, "test@example.com")

    def test_user_profile_post_invalid(self):
        response = self.client.post(
            reverse("user_profile"),
            {
                "email": "invalid-email",  # invalid email format
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/user_profile.html")
        form = response.context["form"]
        self.assertTrue(form.errors)


class CreatorProfileViewTest2(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.profile = CreatorProfile.objects.create(creator=self.creator_user)
        self.client.login(username="creator", password="creatorpass")
        self.url = reverse("creator_profile")

    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    def test_creator_profile_view_get(self, mock_ticket_filter, mock_get_or_create):
        mock_get_or_create.return_value = (self.profile, False)
        mock_ticket_filter.return_value = ["ticket1", "ticket2"]

        response = self.client.get(self.url)

        mock_get_or_create.assert_called_once_with(creator=self.creator_user)
        mock_ticket_filter.assert_called_once_with(user=self.creator_user)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/creator_profile.html")
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CreatorProfileForm)
        self.assertEqual(response.context["tickets"], ["ticket1", "ticket2"])

    @patch("events.models.Ticket.objects.filter")
    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.CreatorProfileForm.is_valid", return_value=True)
    @patch("events.views.CreatorProfileForm.save")
    def test_creator_profile_view_post(
        self, mock_form_save, mock_form_is_valid, mock_get_or_create, mock_ticket_filter
    ):
        mock_get_or_create.return_value = (self.profile, False)
        mock_ticket_filter.return_value = ["ticket1", "ticket2"]

        post_data = {
            "name": "Creator Name",
            "age": 40,
            "bio": "Creator bio",
            "organisation": "Org Name",
            "location": "Creator Location",
            "interests": "Events, Music",
        }

        response = self.client.post(self.url, data=post_data)

        mock_get_or_create.assert_called_once_with(creator=self.creator_user)
        mock_form_is_valid.assert_called_once()
        mock_form_save.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.url)


class CreateEventViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.creator_profile = CreatorProfile.objects.create(creator=self.creator_user)

        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(user=self.user)

        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )

    @patch("boto3.client")
    def test_create_event_with_image(self, mock_boto3_client):
        # Log in as creator
        self.client.login(username="creator", password="creatorpass")

        # Prepare mock S3 client
        mock_s3 = MagicMock()
        mock_boto3_client.return_value = mock_s3

        # Mock image file
        image_content = b"file_content"
        image_file = SimpleUploadedFile(
            "test_image.jpg", image_content, content_type="image/jpeg"
        )

        # Prepare form data
        form_data = {
            "title": "Test Event",
            "description": "This is a test event.",
            "date": "2024-12-10",
            "image": image_file,
        }

        # Send POST request
        response = self.client.post(reverse("create_event"), data=form_data)

        # Assertions
        self.assertEqual(response.status_code, 200)

    @patch("boto3.client")
    def test_create_event_without_image(self, mock_boto3_client):
        # Log in as creator
        self.client.login(username="creator", password="creatorpass")

        # Prepare form data without image
        form_data = {
            "title": "Test Event",
            "description": "This is a test event.",
            "date": "2024-12-10",
        }

        # Send POST request
        _ = self.client.post(reverse("create_event"), data=form_data)

        # Ensure S3 upload is not called
        mock_boto3_client.assert_not_called()

    def test_create_event_get_creator(self):
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("create_event"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/create_event.html")
        self.assertIsInstance(response.context["form"], EventForm)

    @patch("events.views.boto3.client")
    def test_create_event_post_creator_invalid(self, mock_boto_client):
        self.client.login(username="creator", password="creatorpass")
        response = self.client.post(
            reverse("create_event"),
            {
                "name": "",  # name is required
                "location": "",
                "date_time": "",  # invalid date
                "schedule": "",
                "speakers": "",
                "category": "",
                "numTickets": "",  # invalid number
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/create_event.html")
        form = response.context["form"]
        self.assertTrue(form.errors)

    def test_create_event_get_superuser(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("create_event"))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_create_event_as_user(self):
        self.client.login(username="testuser", password="testpass")
        response = self.client.get(reverse("create_event"))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_create_event_unauthenticated(self):
        response = self.client.get(reverse("create_event"))
        login_url = reverse("login") + "?next=" + reverse("create_event")
        self.assertRedirects(response, login_url)


class CreateEventTest(TestCase):
    def setUp(self):
        # Create a user and a creator profile for testing
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.creator_profile = CreatorProfile.objects.create(creator=self.user)
        self.user.creatorprofile = self.creator_profile
        self.client.login(username="testuser", password="testpassword")

    @patch("events.views.boto3.client")
    @patch("events.forms.EventForm.is_valid", return_value=True)
    @patch("events.forms.EventForm.save")
    def test_create_event_with_image(self, mock_save, mock_is_valid, mock_boto_client):
        # Mock S3 client and save method for event
        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3
        mock_event_instance = MagicMock(spec=Event)
        mock_save.return_value = mock_event_instance

        # Simulate POST request with an image file
        image_mock = MagicMock()
        image_mock.name = "test_image.png"
        image_mock.content_type = "image/png"
        form_data = {
            "name": "Test Event",
            "description": "Test Description",
        }
        files_data = {"image": image_mock}

        response = self.client.post(
            reverse("create_event"), data=form_data, files=files_data
        )

        # Check event creation and redirection
        mock_event_instance.save.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("creator_dashboard"))

        # Check that a success message is set
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Event created successfully!" in str(m.message) for m in messages)
        )

    @patch("events.views.boto3.client")
    @patch("events.forms.EventForm.is_valid", return_value=True)
    @patch("events.forms.EventForm.save")
    def test_create_event_without_image(
        self, mock_save, mock_is_valid, mock_boto_client
    ):
        # Mock event instance and bypass S3
        mock_event_instance = MagicMock(spec=Event)
        mock_save.return_value = mock_event_instance

        form_data = {
            "name": "Test Event",
            "description": "Test Description",
        }

        response = self.client.post(reverse("create_event"), data=form_data)

        # S3 should not be called if there's no image
        mock_boto_client.assert_not_called()

        # Check event creation and redirection
        mock_event_instance.save.assert_called_once()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("creator_dashboard"))

        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any("Event created successfully!" in str(m.message) for m in messages)
        )

    def test_create_event_get_request(self):
        response = self.client.get(reverse("create_event"))

        # Check the response status and template used
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/create_event.html")
        self.assertIsInstance(response.context["form"], EventForm)


class DeleteEventViewTest2(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a creator user
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.creator_profile = CreatorProfile.objects.create(creator=self.creator_user)
        # Create another creator user
        self.other_creator_user = User.objects.create_user(
            username="other_creator", password="pass"
        )
        self.other_creator_profile = CreatorProfile.objects.create(
            creator=self.other_creator_user
        )
        # Create a superuser
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        # Create an event
        self.event = Event.objects.create(
            name="Event to Delete",
            location="Location",
            date_time=timezone.now() + timezone.timedelta(days=5),
            schedule="Schedule",
            speakers="Speakers",
            category="Category",
            numTickets=100,
            ticketsSold=0,
            created_by=self.creator_profile,
        )

    def test_delete_event_as_creator(self):
        self.client.login(username="creator", password="creatorpass")
        response = self.client.post(reverse("delete_event", args=[self.event.id]))
        self.assertRedirects(response, reverse("creator_dashboard"))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_delete_event_as_superuser(self):
        self.client.login(username="admin", password="adminpass")
        response = self.client.post(reverse("delete_event", args=[self.event.id]))
        self.assertRedirects(response, reverse("event_list"))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_delete_event_as_other_creator(self):
        self.client.login(username="other_creator", password="pass")
        response = self.client.post(reverse("delete_event", args=[self.event.id]))
        # The event will be deleted because the view does not restrict deletion
        # This may not be desired behavior
        self.assertRedirects(response, reverse("creator_dashboard"))
        self.assertFalse(Event.objects.filter(id=self.event.id).exists())

    def test_delete_event_get_request(self):
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("delete_event", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/delete.html")
        self.assertEqual(response.context["event"], self.event)

    def test_delete_event_unauthenticated(self):
        response = self.client.get(reverse("delete_event", args=[self.event.id]))
        login_url = (
            reverse("login") + "?next=" + reverse("delete_event", args=[self.event.id])
        )
        self.assertRedirects(response, login_url)


class BuyTicketsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="user", password="pass")
        self.profile = UserProfile.objects.create(user=self.user)
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.creator_profile = CreatorProfile.objects.create(creator=self.creator_user)
        self.event = Event.objects.create(
            name="Concert",
            location="Concert Hall",
            date_time=timezone.now() + timezone.timedelta(days=5),
            schedule="Concert Schedule",
            speakers="Band Name",
            category="Music",
            numTickets=100,
            ticketsSold=0,
            created_by=self.creator_profile,
        )
        self.client.login(username="user", password="pass")

    def test_buy_tickets_get(self):
        response = self.client.get(reverse("buy_tickets", args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/buy_tickets.html")
        self.assertIsInstance(response.context["form"], TicketPurchaseForm)

    def test_buy_tickets_post_exceeding_available_tickets(self):
        self.event.numTickets = 1
        self.event.save()
        response = self.client.post(
            reverse("buy_tickets", args=[self.event.id]),
            {"email": "user@example.com", "phone_number": "1234567890", "quantity": 2},
        )
        messages_list = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages_list[0]), "Not enough tickets available!")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/buy_tickets.html")

    def test_buy_tickets_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse("buy_tickets", args=[self.event.id]))
        login_url = (
            reverse("login") + "?next=" + reverse("buy_tickets", args=[self.event.id])
        )
        self.assertRedirects(response, login_url)

    def test_buy_tickets_as_creator(self):
        self.client.logout()
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("buy_tickets", args=[self.event.id]))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_buy_tickets_as_admin(self):
        self.client.logout()
        self.superuser = User.objects.create_superuser(
            username="admin", password="adminpass"
        )
        self.client.login(username="admin", password="adminpass")
        response = self.client.get(reverse("buy_tickets", args=[self.event.id]))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )


class CreatorDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.creator_profile = CreatorProfile.objects.create(creator=self.creator_user)
        self.event = Event.objects.create(
            name="Creator's Event",
            location="Location",
            date_time=timezone.now() + timezone.timedelta(days=5),
            schedule="Schedule",
            speakers="Speakers",
            category="Category",
            numTickets=100,
            ticketsSold=0,
            created_by=self.creator_profile,
        )

    def test_creator_dashboard_authenticated(self):
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("creator_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/creator_dashboard.html")
        self.assertIn(self.event, response.context["events"])

    def test_creator_dashboard_no_events(self):
        self.event.delete()
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("creator_dashboard"))
        self.assertEqual(len(response.context["events"]), 0)

    def test_creator_dashboard_no_creator_profile(self):
        self.creator_profile.delete()
        self.client.login(username="creator", password="creatorpass")
        response = self.client.get(reverse("creator_dashboard"))
        self.assertRedirects(
            response, reverse("not_authorized"), target_status_code=403
        )

    def test_creator_dashboard_unauthenticated(self):
        response = self.client.get(reverse("creator_dashboard"))
        login_url = reverse("login") + "?next=" + reverse("creator_dashboard")
        self.assertRedirects(response, login_url)


class MyTicketsViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="pass")
        self.event = Event.objects.create(
            name="Event with Tickets",
            location="Location",
            date_time=timezone.now() + timezone.timedelta(days=5),
            schedule="Schedule",
            speakers="Speakers",
            category="Category",
            numTickets=100,
            ticketsSold=0,
        )
        Ticket.objects.create(user=self.user, event=self.event, quantity=2)
        self.client = Client()
        self.client.login(username="user", password="pass")


class HomeViewTest(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "events/homepage.html")


class ChatViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.other_user = User.objects.create_user(
            username="otheruser", password="password"
        )
        self.creator_profile = CreatorProfile.objects.create(creator=self.user)
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time=timezone.now(),
            schedule="Sample Schedule",
            speakers="Sample Speaker",
            category="Sample Category",
            created_by=self.creator_profile,
        )
        self.chat_room, created = ChatRoom.objects.get_or_create(
            event=self.event, creator=self.creator_profile
        )

    @patch("events.models.Ticket.objects.filter")
    def test_join_chat_non_creator_with_ticket(self, mock_ticket_filter):
        self.client.login(username="otheruser", password="password")
        mock_ticket_filter.return_value.exists.return_value = True
        url = reverse("join_chat", args=[self.event.id])

        with patch(
            "events.models.RoomMember.objects.get_or_create"
        ) as mock_get_or_create:
            mock_get_or_create.return_value = (MagicMock(is_kicked=False), True)
            response = self.client.get(url)

            self.assertEqual(response.status_code, 302)

    def test_send_message_as_member(self):
        self.client.login(username="testuser", password="password")
        RoomMember.objects.create(room=self.chat_room, user=self.user)
        url = reverse("send_message", args=[self.chat_room.id])
        response = self.client.post(url, {"content": "Hello"})
        self.assertEqual(response.status_code, 200)

    def test_send_message_as_kicked_member(self):
        self.client.login(username="testuser", password="password")
        RoomMember.objects.create(room=self.chat_room, user=self.user, is_kicked=True)
        url = reverse("send_message", args=[self.chat_room.id])
        response = self.client.post(url, {"content": "Hello"})
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            response.content,
            {"error": "You are not allowed to send messages in this chat room."},
        )

    @patch("events.models.ChatMessage.objects.create")
    def test_make_announcement_as_creator(self, mock_message_create):
        self.client.login(username="testuser", password="password")
        url = reverse("make_announcement", args=[self.chat_room.id])
        response = self.client.post(
            url,
            '{"content": "Important announcement"}',
            content_type="application/json",
        )
        mock_message_create.assert_called_once_with(
            room=self.chat_room,
            user=self.user,
            content="[Announcement] Important announcement",
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "success"})

    def test_make_announcement_as_non_creator(self):
        self.client.login(username="otheruser", password="password")
        url = reverse("make_announcement", args=[self.chat_room.id])
        response = self.client.post(
            url, '{"content": "Unauthorized"}', content_type="application/json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(
            response.content, {"error": "You are not authorized to make announcements."}
        )

    @patch("channels.layers.get_channel_layer")
    def test_kick_member_as_creator(self, mock_get_channel_layer):
        self.client.login(username="testuser", password="password")
        RoomMember.objects.create(room=self.chat_room, user=self.other_user)
        url = reverse("kick_member", args=[self.chat_room.id, self.other_user.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            RoomMember.objects.get(room=self.chat_room, user=self.other_user).is_kicked
        )
        self.assertJSONEqual(response.content, {"status": "success"})

    def test_leave_chat(self):
        self.client.login(username="testuser", password="password")
        RoomMember.objects.create(room=self.chat_room, user=self.user)
        url = reverse("leave_chat", args=[self.chat_room.id])
        response = self.client.get(url)
        self.assertRedirects(response, reverse("user_home"))
        self.assertFalse(
            RoomMember.objects.filter(room=self.chat_room, user=self.user).exists()
        )


class FilterWiseDataTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="password")
        self.creator_profile = CreatorProfile.objects.create(creator=self.user)
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time=timezone.now(),
            schedule="Sample Schedule",
            speakers="Sample Speaker",
            category="Sample Category",
            created_by=self.creator_profile,
        )

    @patch("events.models.Ticket.objects.filter")
    def test_fetch_filter_wise_data(self, mock_ticket_filter):
        mock_ticket = MagicMock()
        mock_ticket.created_at = timezone.now() - timedelta(days=1)
        mock_ticket.quantity = 5
        mock_ticket.user_id = self.user.id
        mock_ticket_filter.return_value.filter.return_value = [mock_ticket]

        url = (
            reverse("fetch_filter_wise_data")
            + f"?event_id={self.event.id}&category={self.event.category}"
        )
        response = self.client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("ticket_sales_data", data)
        self.assertIn("unique_users_data", data)
        self.assertEqual(len(data["ticket_sales_data"]), 8)
        self.assertEqual(len(data["unique_users_data"]), 8)


class MapViewTestCase(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = Client()
        self.client.login(username="testuser", password="testpass")

        # Mock current time
        self.current_time = now()

        # Create events
        self.event_with_coordinates = Event.objects.create(
            name="Event With Coordinates",
            location="Location 1",
            date_time=self.current_time,
            latitude=12.3456,
            longitude=78.9012,
            image_url="http://example.com/image.jpg",
            schedule="Event schedule",
        )
        self.event_without_coordinates = Event.objects.create(
            name="Event Without Coordinates",
            location="Location 2",
            date_time=self.current_time,
            latitude=None,
            longitude=None,
            image_url="http://example.com/image2.jpg",
            schedule="Another schedule",
        )

    def test_map_view_renders_correctly(self):
        # Mock the timezone.now function
        with patch("django.utils.timezone.now", return_value=self.current_time):
            response = self.client.get("/mapview/")  # URL of the view

        # Check the response status
        self.assertEqual(response.status_code, 200)

        # Check the rendered template
        self.assertTemplateUsed(response, "events/map_view.html")

        # Check that only events with valid coordinates are included in the context
        events_json = json.loads(response.context["events_json"])
        self.assertEqual(len(events_json), 1)
        self.assertEqual(events_json[0]["id"], self.event_with_coordinates.id)
        self.assertEqual(events_json[0]["name"], "Event With Coordinates")
        self.assertEqual(events_json[0]["latitude"], 12.3456)
        self.assertEqual(events_json[0]["longitude"], 78.9012)
        self.assertEqual(events_json[0]["location"], "Location 1")
        self.assertEqual(events_json[0]["image_url"], "http://example.com/image.jpg")
        self.assertEqual(events_json[0]["description"], "Event schedule")


class JoinChatTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.creator_user = User.objects.create_user(
            username="creator", password="password"
        )
        self.other_user = User.objects.create_user(username="user", password="password")
        self.event_creator_profile = CreatorProfile.objects.create(
            creator=self.creator_user
        )
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time="2024-12-31 18:00:00",
            created_by=self.event_creator_profile,
        )
        self.chat_room_url = reverse("join_chat", kwargs={"event_id": self.event.id})
        self.chat_room, _ = ChatRoom.objects.get_or_create(
            event=self.event, creator=self.event_creator_profile
        )

    def test_creator_joins_chat_room(self):
        # Login as creator
        self.client.login(username="creator", password="password")
        response = self.client.get(self.chat_room_url)
        self.assertRedirects(
            response, reverse("chat_room", kwargs={"room_id": self.chat_room.id})
        )
        self.assertTrue(
            RoomMember.objects.filter(
                room=self.chat_room, user=self.creator_user
            ).exists()
        )

    def test_user_without_ticket_redirected(self):
        # Login as a user who has not purchased a ticket
        self.client.login(username="user", password="password")
        response = self.client.get(self.chat_room_url, follow=True)
        self.assertRedirects(
            response, reverse("event_detail", kwargs={"pk": self.event.id})
        )
        self.assertContains(
            response, "Please purchase a ticket before joining the chat room."
        )

    def test_user_with_ticket_joins_chat_room(self):
        # Create a ticket for the user
        Ticket.objects.create(user=self.other_user, event=self.event)
        self.client.login(username="user", password="password")
        response = self.client.get(self.chat_room_url)
        self.assertRedirects(
            response, reverse("chat_room", kwargs={"room_id": self.chat_room.id})
        )
        self.assertTrue(
            RoomMember.objects.filter(
                room=self.chat_room, user=self.other_user
            ).exists()
        )

    def test_kicked_user_restricted(self):
        # Create a ticket and mark the user as kicked
        RoomMember.objects.create(
            room=self.chat_room, user=self.other_user, is_kicked=True
        )
        self.client.login(username="user", password="password")
        response = self.client.get(self.chat_room_url, follow=True)
        self.assertRedirects(
            response, reverse("event_detail", kwargs={"pk": self.event.id})
        )
