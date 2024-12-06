from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from events.models import Event, Ticket, UserProfile, AdminProfile


class EventModelTest(TestCase):
    def setUp(self):
        self.event = Event.objects.create(
            name="Tech Conference 2024",
            location="Convention Center",
            date_time=timezone.now(),
            schedule="9:00 AM - 10:00 AM: Keynote\n10:00 AM - 11:00 AM: Workshops",
            speakers="John Doe, Jane Smith",
        )

    def test_event_creation(self):
        self.assertTrue(isinstance(self.event, Event))
        self.assertEqual(self.event.__str__(), "Tech Conference 2024")

    def test_event_fields(self):
        self.assertEqual(self.event.name, "Tech Conference 2024")
        self.assertEqual(self.event.location, "Convention Center")
        self.assertIn("Keynote", self.event.schedule)
        self.assertEqual(self.event.speakers, "John Doe, Jane Smith")
        self.assertIsNotNone(self.event.created_at)
        self.assertIsNotNone(self.event.updated_at)

    def test_event_name_max_length(self):
        # Create an event with a name longer than 200 characters
        long_name = "a" * 201  # 201 characters
        event = Event(
            name=long_name,
            location="Convention Center",
            date_time=timezone.now(),
            schedule="Some schedule",
            speakers="John Doe, Jane Smith",
        )
        with self.assertRaises(ValidationError):
            event.full_clean()


class TicketModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user_1", password="12345")
        self.event = Event.objects.create(
            name="Tech Conference 2024",
            location="Convention Center",
            date_time=timezone.now(),
            schedule="9:00 AM - 10:00 AM: Keynote\n10:00 AM - 11:00 AM: Workshops",
            speakers="John Doe, Jane Smith",
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            event=self.event,
            email="testuser@example.com",
            phone_number="1234567890",
            quantity=2,
        )

    def test_ticket_creation(self):
        self.assertTrue(isinstance(self.ticket, Ticket))
        self.assertEqual(
            self.ticket.__str__(), f"{self.event.name} - {self.user.username}"
        )

    def test_ticket_fields(self):
        self.assertEqual(self.ticket.user, self.user)
        self.assertEqual(self.ticket.event, self.event)
        self.assertEqual(self.ticket.email, "testuser@example.com")
        self.assertEqual(self.ticket.phone_number, "1234567890")
        self.assertEqual(self.ticket.quantity, 2)

    def test_ticket_phone_number_max_length(self):
        # Create a ticket with a phone number longer than 12 characters
        long_phone_number = "1" * 13
        ticket = Ticket(
            user=self.user,
            event=self.event,
            email="testuser@example.com",
            phone_number=long_phone_number,
            quantity=2,
        )
        with self.assertRaises(ValidationError):
            ticket.full_clean()


class UserProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="user_2", password="12345")
        self.profile = UserProfile.objects.create(
            user=self.user,
            name="Test User",
            age=25,
            bio="A short bio about the test user.",
            location="New York",
            interests="Technology, Travel",
        )

    def test_user_profile_creation(self):
        self.assertTrue(isinstance(self.profile, UserProfile))
        self.assertEqual(self.profile.__str__(), self.user.username)

    def test_user_profile_fields(self):
        self.assertEqual(self.profile.name, "Test User")
        self.assertEqual(self.profile.age, 25)
        self.assertEqual(self.profile.bio, "A short bio about the test user.")
        self.assertEqual(self.profile.location, "New York")
        self.assertEqual(self.profile.interests, "Technology, Travel")

    def test_user_profile_name_max_length(self):
        user = User.objects.create(username="user_3", password="12345")
        long_name = "a" * 101
        profile = UserProfile(
            user=user,
            name=long_name,
            age=25,
            bio="A short bio about the test user.",
            location="New York",
            interests="Technology, Travel",
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()


class AdminProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="test_admin", password="12345")
        self.profile = AdminProfile.objects.create(
            admin=self.user, email="test_admin@yahoo.com"
        )

    def test_admin_profile_creation(self):
        self.assertTrue(isinstance(self.profile, AdminProfile))
        self.assertEqual(self.profile.__str__(), self.user.username)

    def test_user_profile_fields(self):
        self.assertEqual(self.profile.email, "test_admin@yahoo.com")


# class UserModelTest(TestCase):
#     def test_user_unique_username(self):
#         # Create the first user with username 'user1'
#         User.objects.create(username="user1", password="12345")

#         # Attempt to create another user with the same username
#         with self.assertRaises(IntegrityError):
#             User.objects.create(username="user1", password="67890")

# class CreatorProfileModelTest(TestCase):
#     def test_creator_profile_age_boundaries(self):
#         user = User.objects.create(username="creator", password="12345")
#         profile = CreatorProfile.objects.create(user=user, age=150)
#         self.assertEqual(profile.age, 150)

#     def test_creator_profile_interests_format(self):
#         user = User.objects.create(username="creator", password="12345")
#         profile = CreatorProfile.objects.create(user=user, interests="Art, Music, Tech")
#         self.assertEqual(profile.interests, "Art, Music, Tech")
