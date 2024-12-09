import unittest
from unittest.mock import MagicMock, patch

from django import forms

from events.forms import (
    CreatorProfileForm,
)
from events.forms import email_uniqueness_validator
from events.models import (
    AdminProfile,
    CreatorProfile,
    UserProfile,
)


class TestEmailUniquenessValidator(unittest.TestCase):

    @patch("events.forms.ValidationError")
    def test_email_exists_raises_validation_error(self, mock_validation_error):
        mock_model = MagicMock()

        mock_queryset = MagicMock()
        mock_model.objects.filter.return_value = mock_queryset

        mock_queryset.exists.return_value = True

        with self.assertRaises(forms.ValidationError):
            email_uniqueness_validator("test@example.com", mock_model)

        mock_queryset.exists.assert_called_once()

    def test_email_does_not_exist_no_error(self):
        mock_model = MagicMock()

        mock_queryset = MagicMock()
        mock_model.objects.filter.return_value = mock_queryset

        mock_queryset.exists.return_value = False

        try:
            email_uniqueness_validator("unique@example.com", mock_model)
        except forms.ValidationError:
            self.fail("ValidationError was raised unexpectedly for a unique email.")

        mock_queryset.exists.assert_called_once()

    def test_email_exists_for_different_instance_raises_error(self):
        mock_model = MagicMock()

        mock_instance = MagicMock()
        mock_instance.pk = 1

        mock_queryset = MagicMock()
        mock_model.objects.filter.return_value = mock_queryset

        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.exists.return_value = True

        with self.assertRaises(forms.ValidationError):
            email_uniqueness_validator(
                "test@example.com", mock_model, instance=mock_instance
            )

        mock_queryset.exclude.assert_called_once_with(pk=mock_instance.pk)
        mock_queryset.exists.assert_called_once()

    def test_email_same_instance_no_error(self):

        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_instance.pk = 1

        mock_queryset = MagicMock()
        mock_model.objects.filter.return_value = mock_queryset

        # After excluding the same instance, no records should match
        mock_queryset.exclude.return_value = mock_queryset
        mock_queryset.exists.return_value = False

        # Should not raise any ValidationError
        try:
            email_uniqueness_validator(
                "sameuser@example.com", mock_model, instance=mock_instance
            )
        except forms.ValidationError:
            self.fail("ValidationError was raised unexpectedly for the same instance.")

        mock_queryset.exclude.assert_called_once_with(pk=mock_instance.pk)
        mock_queryset.exists.assert_called_once()


class TestCreatorProfileForm(unittest.TestCase):
    def test_clean_contact_number_valid(self):
        form_data = {
            "organization_name": "My Org",
            "organization_email": "org@example.com",
            "organization_social_media": "http://example.org",
            "contact_number": "1234567890",  # 10 digits, should be valid
        }
        form = CreatorProfileForm(data=form_data)

        self.assertTrue(
            form.is_valid(), "Form should be valid for a correct phone number"
        )
        self.assertEqual(form.cleaned_data["contact_number"], "1234567890")

    def test_clean_contact_number_too_short(self):
        form_data = {
            "organization_name": "My Org",
            "organization_email": "org@example.com",
            "organization_social_media": "http://example.org",
            "contact_number": "123456789",  # 9 digits, too short
        }
        form = CreatorProfileForm(data=form_data)

        self.assertFalse(
            form.is_valid(),
            "Form should be invalid for a phone number that's too short",
        )
        self.assertIn("contact_number", form.errors)
        self.assertIn(
            "Enter a valid phone number (10-12 digits).", form.errors["contact_number"]
        )

    def test_clean_contact_number_too_long(self):
        form_data = {
            "organization_name": "My Org",
            "organization_email": "org@example.com",
            "organization_social_media": "http://example.org",
            "contact_number": "1234567890123",  # 13 digits, too long
        }
        form = CreatorProfileForm(data=form_data)

        self.assertFalse(
            form.is_valid(), "Form should be invalid for a phone number that's too long"
        )
        self.assertIn("contact_number", form.errors)

    def test_clean_contact_number_non_numeric(self):
        form_data = {
            "organization_name": "My Org",
            "organization_email": "org@example.com",
            "organization_social_media": "http://example.org",
            "contact_number": "abc1234567",
        }
        form = CreatorProfileForm(data=form_data)

        self.assertFalse(
            form.is_valid(),
            "Form should be invalid for a phone number with non-numeric characters",
        )
        self.assertIn("contact_number", form.errors)
        self.assertIn(
            "Enter a valid phone number (10-12 digits).", form.errors["contact_number"]
        )

    def test_clean_contact_number_empty(self):
        form_data = {
            "organization_name": "My Org",
            "organization_email": "org@example.com",
            "organization_social_media": "http://example.org",
            "contact_number": "",
        }
        form = CreatorProfileForm(data=form_data)

        self.assertTrue(
            form.is_valid(),
            "Form should be valid even if contact_number is empty if optional",
        )
        self.assertNotIn("contact_number", form.errors)


class TestSendMailNoProfileFound(unittest.TestCase):
    def setUp(self):
        self.form = MagicMock()
        self.form.cleaned_data = {"email": "test@example.com"}

        self.form.get_users = MagicMock(return_value=[MagicMock(username="testuser")])

    @patch("builtins.print")
    def test_creator_profile_does_not_exist_block(self, mock_print):
        user = self.form.get_users()[0]

        type(user).adminprofile = property(
            lambda self: (_ for _ in ()).throw(AdminProfile.DoesNotExist())
        )

        type(user).userprofile = property(
            lambda self: (_ for _ in ()).throw(UserProfile.DoesNotExist())
        )

        type(user).creatorprofile = property(
            lambda self: (_ for _ in ()).throw(CreatorProfile.DoesNotExist())
        )

        self.form.send_mail(
            subject_template_name="subject.txt",
            email_template_name="email.txt",
            context={},
            from_email="from@example.com",
            to_email="to@example.com",
        )


if __name__ == "__main__":
    unittest.main()
