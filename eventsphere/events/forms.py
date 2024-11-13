from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile, CreatorProfile, Event, Ticket

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
        }


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

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
        # "bio": forms.Textarea(attrs={"rows": 3}),
        # "interests": forms.Textarea(attrs={"rows": 3}),
        # }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if (
            email
            and UserProfile.objects.filter(email=email)
            .exclude(pk=self.instance.pk)
            .exists()
        ):
            raise forms.ValidationError("This email is already in use.")
        return email


# class CreatorProfileForm(forms.ModelForm):
#     class Meta:
#         model = CreatorProfile
#         fields = ['organization_name', 'organization_email', 'organization_social_media', 'contact_number']
#         # fields = ["name", "age", "bio", "organisation", "location", "interests"]
#         # widgets = {
#         #     "bio": forms.Textarea(attrs={"rows": 3}),
#         #     "interests": forms.Textarea(attrs={"rows": 2}),
#         # }
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
                    "maxlength": "10",  # Optional attribute for validation
                }
            ),
        }


# class TicketPurchaseForm(forms.ModelForm):
#     class Meta:
#         model = Ticket
#         fields = ["email", "phone_number", "quantity"]
#         widgets = {
#             "quantity": forms.NumberInput(attrs={"min": 1, "max": 5}),
#         }

#     def clean_quantity(self):
#         quantity = self.cleaned_data.get("quantity")
#         if quantity > 5:
#             raise forms.ValidationError("You cannot purchase more than 5 tickets.")
#         return quantity


class TicketPurchaseForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["email", "phone_number", "quantity"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }

    email = forms.EmailField(required=True, max_length=255)
    phone_number = forms.CharField(required=True, max_length=12)

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity > 5:
            raise forms.ValidationError("You cannot purchase more than 5 tickets.")
        return quantity

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get("phone_number")
        if not phone_number.isdigit():
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone_number
