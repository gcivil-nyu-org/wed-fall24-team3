# from django import forms
# from .models import Event
# from django.contrib.auth.models import User
# from django.contrib.auth.forms import UserCreationForm

# class EventForm(forms.ModelForm):
#     class Meta:
#         model = Event
#         fields = ['name', 'location', 'date_time', 'schedule', 'speakers']


# class SignupForm(UserCreationForm):
#     email = forms.EmailField(required=True)

#     class Meta:
#         model = User
#         fields = ('username', 'email', 'password1', 'password2')


from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, Event, Ticket


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ["name", "location", "date_time", "schedule", "speakers"]


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["name", "age", "bio", "location", "interests"]
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 3}),
            "interests": forms.Textarea(attrs={"rows": 3}),
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
