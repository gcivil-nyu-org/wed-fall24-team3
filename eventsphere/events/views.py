from django.shortcuts import render, redirect
from .forms import EventForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
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

@require_POST
@login_required  # Ensure the user is logged in to update the event
def update_event_view(request):
    event_id = request.POST.get('event_id')
    title = request.POST.get('title')
    description = request.POST.get('description')
    date_time = request.POST.get('date_time')

    # Check if the required fields are present
    if not all([event_id, title, description, date_time]):
        return JsonResponse({'error': 'Missing required parameters'}, status=400)

    try:
        # Fetch the event by its ID
        event = Event.objects.get(id=event_id)

        # Check if the logged-in user is the creator of the event
        if event.creator != request.user:
            return JsonResponse({'error': 'You are not allowed to update this event'}, status=403)

        # Update the event details
        event.title = title
        event.description = description
        event.date_time = date_time
        event.save()

        return JsonResponse({'message': 'Event updated successfully'}, status=200)

    except Event.DoesNotExist:
        return JsonResponse({'error': 'Event not found'}, status=404)

def event_success(request):
    return render(request, 'events/event_success.html')