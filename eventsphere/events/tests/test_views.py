from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock, ANY
from events.forms import CreatorProfileForm, UserProfileForm, EventForm
from events.models import Event
from django.core.files.uploadedfile import SimpleUploadedFile


class DeleteEventViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.superuser = User.objects.create_superuser(username='superuser',
                                                       password='superpass')
        
        self.client = Client()
    
    @patch(
        "events.views.get_object_or_404")
    def test_delete_event_as_regular_user_post(self, mock_get_object):
        mock_event = MagicMock()
        mock_get_object.return_value = mock_event
        
        self.client.login(username='testuser', password='testpass')
        
        response = self.client.post(
            reverse('delete_event', args=[1]))  # Event ID is mocked
        
        mock_event.delete.assert_called_once()
        
        self.assertRedirects(response, reverse('creator_dashboard'))
    
    @patch("events.views.get_object_or_404")
    def test_delete_event_as_superuser_post(self, mock_get_object):
        
        mock_event = MagicMock()
        mock_get_object.return_value = mock_event
        
        
        self.client.login(username='superuser', password='superpass')
        
        
        response = self.client.post(
            reverse('delete_event', args=[1]))
        
        
        mock_event.delete.assert_called_once()
        
        
        self.assertRedirects(response, reverse('event_list'))
    
    @patch("events.views.get_object_or_404")
    def test_get_request_renders_delete_confirmation(self, mock_get_object):
        
        mock_event = MagicMock()
        mock_get_object.return_value = mock_event
        
        
        self.client.login(username='testuser', password='testpass')
        
        
        response = self.client.get(
            reverse('delete_event', args=[1]))
        
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/delete.html')
        self.assertIn('event', response.context)
    
    def test_anonymous_user_redirected_to_login(self):
        
        response = self.client.get(
            reverse('delete_event', args=[1]))

        
        self.assertRedirects(response, f'/events/login/?next=/events/delete/1/')


class CreatorProfileViewTest(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
    
    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    def test_get_request_renders_form(self, mock_ticket_filter, mock_get_or_create):
        
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        mock_ticket_filter.return_value = []
        
        
        response = self.client.get(reverse('creator_profile'))
        
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CreatorProfileForm)
        self.assertTemplateUsed(response, 'events/creator_profile.html')
        
        
        mock_ticket_filter.assert_called_once_with(user=self.user)
    
    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.CreatorProfileForm")
    def test_post_request_valid_form(self, mock_form_class, mock_ticket_filter,
                                     mock_get_or_create):
        
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        mock_ticket_filter.return_value = []
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form
        
        
        response = self.client.post(reverse('creator_profile'), data={'field': 'value'})
        
        
        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse('creator_profile'))
    
    @patch("events.views.CreatorProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.CreatorProfileForm")
    def test_post_request_invalid_form(self, mock_form_class, mock_ticket_filter,
                                       mock_get_or_create):
        
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        mock_ticket_filter.return_value = []
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form_class.return_value = mock_form
        
        
        response = self.client.post(reverse('creator_profile'),
                                    data={'field': 'invalid_value'})
        
        
        mock_form.save.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/creator_profile.html')


class UserProfileViewTest(TestCase):
    def setUp(self):
        
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client()
        self.client.login(username='testuser', password='testpass')
    
    @patch("events.views.UserProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    def test_get_request_renders_form_and_groups_tickets(self, mock_ticket_filter,
                                                         mock_get_or_create):
        
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        
        mock_ticket_filter.return_value.values.return_value.annotate.return_value = [
            {"event__name": "Event 1", "event__id": 1, "total_tickets": 3},
            {"event__name": "Event 2", "event__id": 2, "total_tickets": 5},
        ]
        
        
        response = self.client.get(reverse('user_profile'))
        
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], UserProfileForm)
        self.assertTemplateUsed(response, 'events/user_profile.html')
        
        
        mock_ticket_filter.assert_called_once_with(user=self.user)
        self.assertEqual(len(response.context['events_with_tickets']), 2)
    
    @patch("events.views.UserProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.UserProfileForm")
    def test_post_request_valid_form(self, mock_form_class, mock_ticket_filter,
                                     mock_get_or_create):
        
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form_class.return_value = mock_form
        
        
        response = self.client.post(reverse('user_profile'), data={'field': 'value'})
        
        
        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse('user_profile'))
    
    @patch("events.views.UserProfile.objects.get_or_create")
    @patch("events.views.Ticket.objects.filter")
    @patch("events.views.UserProfileForm")
    def test_post_request_invalid_form(self, mock_form_class, mock_ticket_filter,
                                       mock_get_or_create):
        
        mock_profile = MagicMock()
        mock_get_or_create.return_value = (mock_profile, False)
        
        mock_form = MagicMock()
        mock_form.is_valid.return_value = False
        mock_form_class.return_value = mock_form
        
        
        response = self.client.post(reverse('user_profile'),
                                    data={'field': 'invalid_value'})
        
        
        mock_form.save.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/user_profile.html')


class UpdateEventViewTest(TestCase):
    def setUp(self):
        # Set up a test user and superuser
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.superuser = User.objects.create_superuser(username='superuser',
                                                       password='superpass')
        
        # Initialize the client for testing
        self.client = Client()
    
    @patch("events.views.get_object_or_404")
    @patch("events.views.EventForm")
    def test_get_request_renders_form(self, mock_event_form, mock_get_object):
        # Mock the event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event
        
        # Mock the form instance
        mock_form_instance = MagicMock()
        mock_event_form.return_value = mock_form_instance
        
        # Log in as a regular user
        self.client.login(username='testuser', password='testpass')
        
        # Send a GET request
        response = self.client.get(reverse('update_event', args=[mock_event.id]))
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'events/update_event.html')
        self.assertEqual(response.context['form'], mock_form_instance)
        
        # Ensure get_object_or_404 was called with correct arguments
        mock_get_object.assert_called_once_with(Event, id=mock_event.id)
    
    @patch("events.views.get_object_or_404")
    @patch("events.views.boto3.client")
    @patch("events.views.EventForm")
    def test_post_request_valid_form_no_image(self, mock_event_form, mock_boto_client,
                                              mock_get_object):
        # Mock the event retrieval
        mock_event = MagicMock()
        mock_event.id = 1  # Set a real integer for event ID
        mock_get_object.return_value = mock_event
        
        # Mock the form validation and save
        mock_form = MagicMock()
        mock_form.is_valid.return_value = True
        mock_form.save.return_value = mock_event
        mock_event_form.return_value = mock_form
        
        # Log in as a regular user
        self.client.login(username='testuser', password='testpass')
        
        # Send a POST request without an image
        response = self.client.post(reverse('update_event', args=[mock_event.id]),
                                    data={'name': 'Updated Event'})
        
        # Ensure form.save() was called and redirection to creator_dashboard
        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse('creator_dashboard'))
    
    @patch("events.views.get_object_or_404")
    @patch("events.views.boto3.client")
    @patch("events.views.EventForm")
    def test_post_request_valid_form_with_image(self, mock_event_form, mock_boto_client,
                                                mock_get_object):
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
            name="test_image.jpg",
            content=b"file_content",
            content_type="image/jpeg"
        )
        
        # Log in as a superuser
        self.client.login(username='superuser', password='superpass')
        
        # Send a POST request with an image
        response = self.client.post(
            reverse('update_event', args=[mock_event.id]),
            data={'name': 'Updated Event', 'image': image_mock},
            format='multipart'
        )
        
        # Verify image upload to S3
        mock_s3.upload_fileobj.assert_called_once_with(
            ANY,  # Ignore the exact file type, just ensure it's passed as a file object
            "eventsphere-images",
            "events/test_image.jpg",
            ExtraArgs={"ContentType": "image/jpeg"}
        )
        # Ensure form.save() was called and user is redirected to event_list
        mock_form.save.assert_called_once()
        self.assertRedirects(response, reverse('event_list'))
    
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
        self.client.login(username='testuser', password='testpass')
        
        # Send a POST request with invalid data
        response = self.client.post(reverse('update_event', args=[mock_event.id]),
                                    data={'name': ''})
        
        # Ensure form.save() was not called, and form is re-rendered with 400 status
        mock_form.save.assert_not_called()
        self.assertEqual(response.status_code, 400)
        self.assertTemplateUsed(response, 'events/update_event.html')
        self.assertIn('errors', response.context)
