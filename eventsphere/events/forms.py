from django import forms
from .models import Event
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'location', 'date_time', 'schedule', 'speakers']


class SignupForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
