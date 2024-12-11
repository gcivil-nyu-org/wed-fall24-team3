from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.core import mail
from django.urls import reverse
from events.forms import (
    CreatorProfileForm,
    UserProfileForm,
    EventForm,
    TicketPurchaseForm,
    SignupForm,
)
from events.models import (
    AdminProfile,
    CreatorProfile,
    UserProfile,
)


class FormValidatorTests(TestCase):
    def setUp(self):
        # Set up a test user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.profile = UserProfile.objects.create(
            user=self.user, email="user@example.com"
        )

        # Set up a creator
        self.creator_user = User.objects.create_user(
            username="creator", password="creatorpass"
        )
        self.creator_profile = CreatorProfile.objects.create(
            creator=self.creator_user,
            organization_email="creator@example.com",
            contact_number="1234567890",
        )

        # Initialize the client for testing
        self.client = Client()

    def test_signup_form_validators(self):
        # Test valid data
        form = SignupForm(
            data={
                "username": "newuser",
                "email": "newuser@example.com",
                "password1": "newuserpass123",
                "password2": "newuserpass123",
            }
        )
        # print(form.errors)
        self.assertTrue(form.is_valid())

        # Test invalid email
        form = SignupForm(
            data={
                "username": "newuser",
                "email": "",
                "password1": "password12345",
                "password2": "password12345",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Email is required.", form.errors["email"])

    def test_user_profile_form_validators(self):
        # Test positive age
        form = UserProfileForm(
            data={
                "name": "Test User",
                "age": 30,
                "bio": "Test bio",
                "location": "Test location",
                "email": "validemail@example.com",
            }
        )
        self.assertTrue(form.is_valid())

        # Test invalid age
        form = UserProfileForm(
            data={
                "name": "Test User",
                "age": -5,
                "bio": "Test bio",
                "location": "Test location",
                "email": "validemail@example.com",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Age must be a positive number.", form.errors["age"])

        form = UserProfileForm(
            data={
                "name": "Test User",
                "age": 1005,
                "bio": "Test bio",
                "location": "Test location",
                "email": "validemail@example.com",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Come on, nobody's THAT old!", form.errors["age"])

        # Test email uniqueness
        form = UserProfileForm(
            data={
                "name": "Another User",
                "age": 25,
                "bio": "Test bio",
                "location": "Test location",
                "email": "user@example.com",  # Duplicate email
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("This email is already in use.", form.errors["email"])

    def test_creator_profile_form_validators(self):
        # Test valid data
        form = CreatorProfileForm(
            data={
                "organization_name": "Test Org",
                "organization_email": "neworg@example.com",
                "organization_social_media": "http://example.com",
                "contact_number": "9876543210",
            }
        )
        self.assertTrue(form.is_valid())

        # Test invalid contact number
        form = CreatorProfileForm(
            data={
                "organization_name": "Test Org",
                "organization_email": "neworg@example.com",
                "organization_social_media": "http://example.com",
                "contact_number": "123",  # Invalid number
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Enter a valid phone number (10-12 digits).", form.errors["contact_number"]
        )

    def test_event_form_validators(self):
        # Test valid data
        form = EventForm(
            data={
                "name": "Test Event",
                "location": "Test Location",
                "date_time": "2024-12-31 18:00:00",
                "schedule": "Test Schedule",
                "speakers": "Test Speaker",
                "category": "Entertainment",
                "latitude": 12.34,
                "longitude": 56.78,
                "numTickets": 100,
            }
        )
        self.assertTrue(form.is_valid())

        # Test missing required field
        form = EventForm(
            data={
                "name": "",
                "location": "Test Location",
                "date_time": "2024-12-31 18:00:00",
                "schedule": "Test Schedule",
                "speakers": "Test Speaker",
                "category": "Entertainment",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("This field is required.", form.errors["name"])

    def test_ticket_purchase_form_validators(self):
        # Test valid data
        form = TicketPurchaseForm(
            data={
                "email": "buyer@example.com",
                "phone_number": "1234567890",
                "quantity": 3,
            }
        )
        self.assertTrue(form.is_valid())

        # Test invalid quantity
        form = TicketPurchaseForm(
            data={
                "email": "buyer@example.com",
                "phone_number": "1234567890",
                "quantity": 10,  # Invalid quantity
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("You can only purchase 1 to 5 tickets.", form.errors["quantity"])


class ForgotPasswordTest(TestCase):
    def setUp(self):
        """
        Set up users with different profiles for testing.
        """
        # Create Admin user
        self.admin_user = User.objects.create_user(
            username="adminuser", password="adminpass"
        )
        AdminProfile.objects.create(
            admin=self.admin_user, email="adminuser@yopmail.com"
        )

        # Create Regular User
        self.regular_user = User.objects.create_user(
            username="regularuser", password="userpass"
        )
        UserProfile.objects.create(
            user=self.regular_user, email="regularuser@yopmail.com"
        )

        # Create Creator user
        self.creator_user = User.objects.create_user(
            username="creatoruser", password="creatorpass"
        )
        CreatorProfile.objects.create(
            creator=self.creator_user, organization_email="creatoruser@yopmail.com"
        )

    def test_password_reset_admin_user(self):
        """
        Test that an admin user can reset their password and receives the email at AdminProfile.email.
        """
        response = self.client.post(
            reverse("password_reset"), {"email": "adminuser@yopmail.com"}
        )
        # Check redirect to 'password_reset_done'
        self.assertRedirects(response, reverse("password_reset_done"))
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        # Verify email details
        email = mail.outbox[0]
        self.assertIn("Password Reset Requested for EventSphere Account", email.subject)
        self.assertIn("adminuser@yopmail.com", email.to)
        self.assertIn("Hi adminuser,", email.body)

    def test_password_reset_regular_user(self):
        """
        Test that a regular user can reset their password and receives the email at UserProfile.email.
        """
        response = self.client.post(
            reverse("password_reset"), {"email": "regularuser@yopmail.com"}
        )
        # Check redirect to 'password_reset_done'
        self.assertRedirects(response, reverse("password_reset_done"))
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        # Verify email details
        email = mail.outbox[0]
        self.assertIn("Password Reset Requested for EventSphere Account", email.subject)
        self.assertIn("regularuser@yopmail.com", email.to)
        self.assertIn("Hi regularuser,", email.body)

    def test_password_reset_creator_user(self):
        """
        Test that a creator can reset their password and receives the email at CreatorProfile.organization_email.
        """
        response = self.client.post(
            reverse("password_reset"), {"email": "creatoruser@yopmail.com"}
        )
        # Check redirect to 'password_reset_done'
        self.assertRedirects(response, reverse("password_reset_done"))
        # Check that one email was sent
        self.assertEqual(len(mail.outbox), 1)
        # Verify email details
        email = mail.outbox[0]
        self.assertIn("Password Reset Requested for EventSphere Account", email.subject)
        self.assertIn("creatoruser@yopmail.com", email.to)
        self.assertIn("Hi creatoruser,", email.body)

    def test_password_reset_non_existing_email(self):
        """
        Test that requesting a password reset with a non-existent email shows an appropriate error.
        """
        response = self.client.post(
            reverse("password_reset"), {"email": "nonexistent@yopmail.com"}
        )
        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"], ["No user is associated with this email address."]
        )
        # Ensure no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_invalid_email_format(self):
        """
        Test that entering an invalid email format shows form validation errors.
        """
        response = self.client.post(
            reverse("password_reset"), {"email": "invalid-email"}
        )
        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], ["Enter a valid email address."])
        # Ensure no email was sent
        self.assertEqual(len(mail.outbox), 0)

    # def test_password_reset_link_is_valid(self):
    #     """
    #     Test that the password reset link sent via email is valid and can be used to reset the password.
    #     """
    #     # Initiate password reset
    #     response = self.client.post(reverse('password_reset'), {'email': 'adminuser@yopmail.com'})
    #     self.assertRedirects(response, reverse('password_reset_done'))
    #     self.assertEqual(len(mail.outbox), 1)

    #     # Extract the reset link from the email
    #     email = mail.outbox[0]
    #     # Use regex to find the URL in the email body
    #     reset_link_match = re.search(r'http[s]?://[^ \n]+', email.body)
    #     self.assertIsNotNone(reset_link_match, "No reset link found in the email.")
    #     reset_link = reset_link_match.group(0)

    #     # Convert the absolute URL to a relative path
    #     domain = 'http://localhost:8000'
    #     self.assertTrue(reset_link.startswith(domain), "Reset link does not start with expected domain.")
    #     reset_path = reset_link.replace(domain, '')

    #     # Access the reset link
    #     response = self.client.get(reset_path)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, "Set a New Password")

    #     # Submit the new password
    #     new_password = 'newadminpass123'
    #     response = self.client.post(reset_path, {
    #         'new_password1': new_password,
    #         'new_password2': new_password
    #     })
    #     self.assertRedirects(response, reverse('password_reset_complete'))

    #     # Attempt to log in with the new password
    #     login = self.client.login(username='adminuser', password=new_password)
    #     self.assertTrue(login)

    # def test_password_reset_link_invalid_token(self):
    #     """
    #     Test that accessing a password reset link with an invalid token is handled properly.
    #     """
    #     # Generate a valid uid
    #     uid = urlsafe_base64_encode(force_bytes(self.admin_user.pk))
    #     # Use an invalid token
    #     token = 'invalid-token'
    #     reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

    #     # Access the reset link with invalid token
    #     response = self.client.get(reset_url)
    #     self.assertEqual(response.status_code, 200)
    #     # Check that the appropriate error message is displayed
    #     self.assertContains(response, "The reset password link is no longer valid.", status_code=200)

    def test_password_reset_no_profile_email(self):
        """
        Test that requesting a password reset for a user without a profile email does not send an email.
        """
        # Create a user without a profile email
        User.objects.create_user(username="noprofuser", password="noprofpass")
        # Do not create a profile for this user
        response = self.client.post(
            reverse("password_reset"), {"email": "noprofuser@yopmail.com"}
        )
        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(
            form.errors["email"], ["No user is associated with this email address."]
        )
        # Ensure no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_profile_email_empty(self):
        """
        Test that requesting a password reset with an empty email field shows appropriate errors.
        """
        # Create a user with an empty profile email
        user = User.objects.create_user(username="emptyemailuser", password="emptypass")
        UserProfile.objects.create(user=user, email="")

        response = self.client.post(reverse("password_reset"), {"email": ""})
        # Check that the form is re-rendered with errors
        self.assertEqual(response.status_code, 200)
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertEqual(form.errors["email"], ["This field is required."])
        # Ensure no email was sent
        self.assertEqual(len(mail.outbox), 0)

    def test_password_reset_email_contains_reset_link(self):
        """
        Test that the password reset email contains a valid reset link.
        """
        response = self.client.post(
            reverse("password_reset"), {"email": "adminuser@yopmail.com"}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]
        # Check that the email body contains a URL
        self.assertRegex(email.body, r"http[s]?://[^ \n]+")

    def tearDown(self):
        """
        Clean up after tests.
        """
        mail.outbox = []
