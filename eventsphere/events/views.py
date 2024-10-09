from django.shortcuts import get_object_or_404, render, redirect
from .forms import EventForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Event

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from .forms import EventForm
# events/views.py
from .models import Event


def home(request):
    return render(request, 'events/home.html')

def event_list(request):
    events = Event.objects.all()
    return render(request, 'events/event_list.html', {'events': events})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after signup
            return redirect('event_list')  # Redirect to create_event or any page you prefer
    else:
        form = UserCreationForm()
    return render(request, 'events/signup.html', {'form': form})

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_list')  # Redirect to the success page after form submission
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})

def update_event_view(request, event_id):
    # Fetch the event by its ID
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)  # Pass the event instance to the form
        if form.is_valid():
            form.save()
            return redirect('event_list')  # Redirect to the event list page after successful update
        else:
            return render(request, 'events/update_event.html', {'form': form, 'errors': form.errors}, status=400)
    else:
        form = EventForm(instance=event)  # Pre-fill the form with the event data
    
    return render(request, 'events/update_event.html', {'form': form})
    
def event_success(request):
    return render(request, 'events/event_success.html')