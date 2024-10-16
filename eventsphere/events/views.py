from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q

# events/views.py
from django.shortcuts import render, get_object_or_404, redirect

from .forms import EventForm
from .models import Event


def user_home(request):
    return render(request, "events/user_home.html")


def home(request):
    return render(request, "events/home.html")


def user_event_list(request):
    query = request.GET.get("q")
    events = Event.objects.all()
    if query:
        events = events.filter(
            Q(name__icontains=query)
            | Q(location__icontains=query)
            | Q(speakers__icontains=query)
        )
    return render(
        request, "events/user_event_list.html", {"events": events, "query": query}
    )


@login_required
def event_list(request):
    events = Event.objects.all()
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, "events/event_detail.html", {"event": event})


def user_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            login(request, user)
            return redirect("user_home")
    else:
        form = UserCreationForm()
    return render(request, "events/user_signup.html", {"form": form})


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_staff = True
            user.is_superuser = True
            user.save()
            login(request, user)
            return redirect(
                "event_list"
            )  # Redirect to create_event or any page you prefer
    else:
        form = UserCreationForm()
    return render(request, "events/signup.html", {"form": form})


@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(
                "event_list"
            )  # Redirect to the success page after form submission
    else:
        form = EventForm()
    return render(request, "events/create_event.html", {"form": form})


def update_event_view(request, event_id):
    # Fetch the event by its ID
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = EventForm(
            request.POST, instance=event
        )  # Pass the event instance to the form
        if form.is_valid():
            form.save()
            return redirect(
                "event_list"
            )  # Redirect to the event list page after successful update
        else:
            return render(
                request,
                "events/update_event.html",
                {"form": form, "errors": form.errors},
                status=400,
            )
    else:
        form = EventForm(instance=event)  # Pre-fill the form with the event data

    return render(request, "events/update_event.html", {"form": form})


def event_success(request):
    return render(request, "events/event_success.html")


@login_required  # Ensure only logged-in users can delete events
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        event.delete()
        return redirect("event_list")  # Redirect to a success page after deletion

    return render(request, "events/delete.html", {"event": event})
