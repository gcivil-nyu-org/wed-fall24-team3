from django.shortcuts import render, redirect
from .forms import EventForm

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

from django.contrib.auth.decorators import login_required
from .forms import EventForm

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after signup
            return redirect('create_event')  # Redirect to create_event or any page you prefer
    else:
        form = UserCreationForm()
    return render(request, 'events/signup.html', {'form': form})

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_success')  # Redirect to the success page after form submission
    else:
        form = EventForm()
    return render(request, 'events/create_event.html', {'form': form})


def event_success(request):
    return render(request, 'events/event_success.html')