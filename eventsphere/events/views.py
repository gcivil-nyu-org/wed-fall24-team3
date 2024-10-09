from django.shortcuts import get_object_or_404, render, redirect
from .forms import EventForm
from django.contrib.auth.models import User
from django.http import JsonResponse
from .models import Event

def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('event_success')  # Redirect to the success page after form submission
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
            return JsonResponse({'message': 'Event updated successfully'}, status=200)
        else:
            return JsonResponse({'error': form.errors}, status=400)  # Return form validation errors
    else:
        form = EventForm(instance=event)  # Pre-fill the form with the event data
    
    return render(request, 'events/update_event.html', {'form': form})
    
def event_success(request):
    return render(request, 'events/event_success.html')