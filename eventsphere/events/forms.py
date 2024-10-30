from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, CreatorProfile, Event, Ticket


class EventForm(forms.ModelForm):
    image = forms.ImageField(required=False)  # Field for uploading the image

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
            "bio": forms.Textarea(attrs={"rows": 3}),
            "interests": forms.Textarea(attrs={"rows": 3}),
        }

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


class CreatorProfileForm(forms.ModelForm):
    class Meta:
        model = CreatorProfile
        fields = ["name", "age", "bio", "organisation", "location", "interests"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "interests": forms.Textarea(attrs={"rows": 2}),
        }


class TicketPurchaseForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["email", "phone_number", "quantity"]
        widgets = {
            "quantity": forms.NumberInput(attrs={"min": 1, "max": 5}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity")
        if quantity > 5:
            raise forms.ValidationError("You cannot purchase more than 5 tickets.")
        return quantity
