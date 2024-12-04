from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MaxLengthValidator
from django.core.exceptions import ValidationError
from django import forms
from .models import AdminProfile, UserProfile, CreatorProfile, Event, Ticket


phone_number_validator = RegexValidator(
    r"^\d{10,12}$", "Enter a valid phone number (10-12 digits)."
)


def email_uniqueness_validator(email, model, instance=None):
    queryset = model.objects.filter(email=email)
    if instance:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.exists():
        raise forms.ValidationError("This email is already in use.")


EVENT_CATEGORIES = [
    ("Entertainment", "Entertainment"),
    ("Business", "Business"),
    ("Sports", "Sports"),
    ("Technology", "Technology"),
    ("Travel", "Travel"),
    ("Food", "Food"),
]


class EventForm(forms.ModelForm):
    image = forms.ImageField(required=False)
    category = forms.ChoiceField(choices=EVENT_CATEGORIES)  # Dropdown for categories

    class Meta:
        model = Event
        fields = [
            "name",
            "location",
            "date_time",
            "schedule",
            "speakers",
            "category",
            "latitude",
            "longitude",
            "image",
            "numTickets",
        ]
        widgets = {
            "latitude": forms.HiddenInput(),
            "longitude": forms.HiddenInput(),
            "date_time": forms.DateTimeInput(
                attrs={"class": "form-control datetimepicker"}
            ),
        }


class SignupForm(UserCreationForm):
    username = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter your username"}
        ),
        validators=[MaxLengthValidator(255)],
        error_messages={
            "required": "Username is required.",
            "max_length": "Username cannot exceed 255 characters.",
        },
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Enter your email"}
        ),
        error_messages={"required": "Email is required."},
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            "name",
            "age",
            "bio",
            "location",
            "interests",
            "email",
        ]  # Include email field
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3, "placeholder": "Add a short bio"}),
            "location": forms.TextInput(attrs={"placeholder": "Enter your location"}),
            "name": forms.TextInput(attrs={"placeholder": "Enter your name"}),
            "age": forms.NumberInput(attrs={"placeholder": "Enter your age"}),
            "email": forms.EmailInput(attrs={"placeholder": "Enter your email"}),
            "interests": forms.TextInput(
                attrs={"rows": 3, "placeholder": "Enter your interests"}
            ),
        }
        interests = forms.CharField(required=False)
        bio = forms.CharField(required=False)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            email_uniqueness_validator(email, UserProfile, self.instance)
        return email

    def clean_age(self):
        age = self.cleaned_data.get("age")
        if age is not None and age <= 0:  # Validate positive age
            raise ValidationError("Age must be a positive number.")
        if age is not None and age >= 150:
            raise ValidationError("Come on, nobody's THAT old!")
        return age


class CreatorProfileForm(forms.ModelForm):
    class Meta:
        model = CreatorProfile
        fields = [
            "organization_name",
            "organization_email",
            "organization_social_media",
            "contact_number",
        ]
        widgets = {
            "organization_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your organization name",
                    "class": "form-control",
                }
            ),
            "organization_email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter your organization email",
                    "class": "form-control",
                }
            ),
            "organization_social_media": forms.URLInput(
                attrs={
                    "placeholder": "Enter your organization’s social media link",
                    "class": "form-control",
                }
            ),
            "contact_number": forms.TextInput(
                attrs={
                    "placeholder": "Enter your contact number",
                    "class": "form-control",
                    "maxlength": "12",  # Optional attribute for validation
                }
            ),
        }

    def clean_contact_number(self):
        contact_number = self.cleaned_data.get("contact_number")
        if contact_number:
            phone_number_validator(contact_number)
        return contact_number


class TicketPurchaseForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["email", "phone_number", "quantity"]

    email = forms.EmailField(
        required=True,
        max_length=255,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your email",
            }
        ),
        error_messages={
            "required": "Please enter your email.",
            "invalid": "Enter a valid email address.",
        },
    )
    phone_number = forms.CharField(
        required=True,
        max_length=12,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your phone number",
            }
        ),
        validators=[phone_number_validator],
    )
    quantity = forms.IntegerField(
        widget=forms.NumberInput(attrs={"min": 1, "max": 5, "class": "form-control"}),
        error_messages={"invalid": "Enter a valid quantity."},
    )

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if not (1 <= quantity <= 5):
            raise forms.ValidationError("You can only purchase 1 to 5 tickets.")
        return quantity
    
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label="Email", max_length=254, required=True)

    def clean_email(self):
        email = self.cleaned_data['email']
        users = set()

        # Search in AdminProfile
        admin_users = AdminProfile.objects.filter(email__iexact=email).values_list('admin', flat=True)
        users.update(User.objects.filter(id__in=admin_users))

        # Search in UserProfile
        user_users = UserProfile.objects.filter(email__iexact=email).values_list('user', flat=True)
        users.update(User.objects.filter(id__in=user_users))

        # Search in CreatorProfile (organization_email)
        creator_users = CreatorProfile.objects.filter(organization_email__iexact=email).values_list('creator', flat=True)
        users.update(User.objects.filter(id__in=creator_users))

        if not users:
            raise ValidationError("No user is associated with this email address.")

        self.users_cache = users  # Cache the users for use in the view
        return email

    def get_users(self, email):
        return self.users_cache
    
    def send_mail(self, subject_template_name, email_template_name,
                context, from_email, to_email, html_email_template_name=None):
        for user in self.get_users(self.cleaned_data['email']):
            try:
                admin_profile = user.adminprofile
                profile_email = admin_profile.email
                print(f"Sending email to AdminProfile email: {profile_email}")
            except AdminProfile.DoesNotExist:
                try:
                    user_profile = user.userprofile
                    profile_email = user_profile.email
                    print(f"Sending email to UserProfile email: {profile_email}")
                except UserProfile.DoesNotExist:
                    try:
                        creator_profile = user.creatorprofile
                        profile_email = creator_profile.organization_email
                        print(f"Sending email to CreatorProfile email: {profile_email}")
                    except CreatorProfile.DoesNotExist:
                        print("No profile found for user:", user.username)
                        continue

            if profile_email:
                try:
                    super().send_mail(subject_template_name, email_template_name,
                                    context, from_email, profile_email, html_email_template_name)
                    print(f"Email sent to {profile_email}")
                except Exception as e:
                    print(f"Failed to send email to {profile_email}: {e}")

