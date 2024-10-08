from django.shortcuts import render, redirect
from .forms import EventForm

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