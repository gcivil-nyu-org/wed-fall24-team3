from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm

# from django.contrib.auth.models import User
from django.db.models import Q
from .models import UserProfile, CreatorProfile, Ticket, Event
from .forms import UserProfileForm, CreatorProfileForm
from django.shortcuts import render, get_object_or_404, redirect
from .forms import EventForm
from .forms import TicketPurchaseForm
from django.contrib import messages


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
def creator_dashboard(request):
    try:
        creator_profile = CreatorProfile.objects.get(creator=request.user)
    except CreatorProfile.DoesNotExist:
        # Handle case where logged-in user doesn't have a CreatorProfile
        creator_profile = None

    if creator_profile:
        # Get all events created by the logged-in user's creator profile
        events = Event.objects.filter(created_by=creator_profile)
    else:
        # If no creator profile exists, return an empty queryset
        events = Event.objects.none()

    return render(request, "events/creator_dashboard.html", {"events": events})


@login_required
def event_list(request):
    events = Event.objects.all()
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, pk):
    event = get_object_or_404(Event, pk=pk)
    return render(request, "events/event_detail.html", {"event": event})


# All signups
def user_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            login(request, user)
            return redirect("user_profile")
    else:
        form = UserCreationForm()
    return render(request, "events/user_signup.html", {"form": form})


def creator_signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            creator = form.save(commit=False)
            creator.is_staff = True
            creator.is_superuser = False
            creator.save()
            login(request, creator)
            return redirect("creator_profile")
    else:
        form = UserCreationForm()
    return render(request, "events/creator_signup.html", {"form": form})


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
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
def creator_creates_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user.creatorprofile
            event.save()
            events = Event.objects.filter(created_by=request.user.creatorprofile)
            return render(request, "events/creator_dashboard.html", {"events": events})
    else:
        form = EventForm()
    return render(request, "events/creator_creates_event.html", {"form": form})


@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user.creatorprofile
            event.save()
            events = Event.objects.all()
            return render(request, "events/event_list.html", {"events": events})
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
            if request.user.is_superuser:
                return redirect(
                    "event_list"
                )  # Redirect to the event list page after successful update
            return redirect("creator_dashboard")
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


@login_required
def user_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("user_profile")
    else:
        form = UserProfileForm(instance=profile)

    # Fetch the tickets for the current user
    tickets = Ticket.objects.filter(user=request.user)

    return render(
        request, "events/user_profile.html", {"form": form, "tickets": tickets}
    )


@login_required
def creator_profile(request):
    profile, created = CreatorProfile.objects.get_or_create(creator=request.user)

    if request.method == "POST":
        form = CreatorProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("creator_profile")
    else:
        form = CreatorProfileForm(instance=profile)

    # Fetch the tickets for the current user
    tickets = Ticket.objects.filter(user=request.user)

    return render(
        request, "events/creator_profile.html", {"form": form, "tickets": tickets}
    )


@login_required
def my_tickets(request):
    tickets = Ticket.objects.filter(user=request.user)
    return render(request, "events/my_tickets.html", {"tickets": tickets})


@login_required
def buy_tickets(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = TicketPurchaseForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.user = request.user
            ticket.event = event

            if event.numTickets >= ticket.quantity:
                event.numTickets = event.numTickets - ticket.quantity
                event.save()  # Save the updated event object
                # to reflect the new numTickets value
                ticket.save()  # Save the ticket after event has been updated
                messages.success(request, "Ticket purchased successfully!")
                return redirect("user_profile")
            else:
                messages.error(request, "Not enough tickets available.")
    else:
        form = TicketPurchaseForm()

    return render(request, "events/buy_tickets.html", {"event": event, "form": form})
