from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse

from events.models import UserProfile, Ticket, Event
from events.views import user_profile


class UserProfileViewTest(TestCase):
    def setUp(self):
        # Create a test user and log them in
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.user_profile = UserProfile.objects.create(user=self.user)

        # Create a test event and ticket
        self.event = Event.objects.create(
            name="Test Event",
            location="Test Location",
            date_time="2024-10-24 10:00:00",
            schedule="Test Schedule",
            speakers="Test Speaker",
        )
        self.ticket = Ticket.objects.create(
            user=self.user, event=self.event, quantity=3
        )

    @patch("events.forms.UserProfileForm.is_valid", return_value=True)
    @patch("events.forms.UserProfileForm.save", return_value=None)
    def test_user_profile_post(self, mock_save, mock_is_valid):
        # Simulate a POST request with valid form data
        form_data = {
            "name": "Updated Name",
            "bio": "Updated bio",
            # Add other form fields as needed
        }
        request = self.factory.post(reverse("user_profile"), data=form_data)
        request.user = self.user

        response = user_profile(request)

        # Check that the response is a redirect (HTTP status 302)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_profile"))

        # Ensure the form's `is_valid()` and `save()` were called
        mock_is_valid.assert_called_once()
        mock_save.assert_called_once()
