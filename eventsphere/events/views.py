# from django.contrib.auth import login
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.forms import UserCreationForm
# from django.db.models import Q
# from .models import UserProfile, Ticket, Event
# from .forms import UserProfileForm
# from django.shortcuts import render, get_object_or_404, redirect
# from .forms import EventForm
# from .forms import TicketPurchaseForm
# from django.contrib import messages


# def user_home(request):
#     return render(request, "events/user_home.html")


# def home(request):
#     return render(request, "events/home.html")


# def user_event_list(request):
#     query = request.GET.get("q")
#     events = Event.objects.all()
#     if query:
#         events = events.filter(
#             Q(name__icontains=query)
#             | Q(location__icontains=query)
#             | Q(speakers__icontains=query)
#         )
#     return render(
#         request, "events/user_event_list.html", {"events": events, "query": query}
#     )


# @login_required
# def event_list(request):
#     events = Event.objects.all()
#     return render(request, "events/event_list.html", {"events": events})


# def event_detail(request, pk):
#     event = get_object_or_404(Event, pk=pk)
#     return render(request, "events/event_detail.html", {"event": event})


# def user_signup(request):
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save(commit=False)
#             user.is_staff = False
#             user.is_superuser = False
#             user.save()
#             login(request, user)
#             return redirect("user_home")
#     else:
#         form = UserCreationForm()
#     return render(request, "events/user_signup.html", {"form": form})


# def signup(request):
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             user.is_staff = True
#             user.is_superuser = True
#             user.save()
#             login(request, user)
#             return redirect(
#                 "event_list"
#             )  # Redirect to create_event or any page you prefer
#     else:
#         form = UserCreationForm()
#     return render(request, "events/signup.html", {"form": form})


# @login_required
# def create_event(request):
#     if request.method == "POST":
#         form = EventForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect(
#                 "event_list"
#             )  # Redirect to the success page after form submission
#     else:
#         form = EventForm()
#     return render(request, "events/create_event.html", {"form": form})


# def update_event_view(request, event_id):
#     # Fetch the event by its ID
#     event = get_object_or_404(Event, id=event_id)

#     if request.method == "POST":
#         form = EventForm(
#             request.POST, instance=event
#         )  # Pass the event instance to the form
#         if form.is_valid():
#             form.save()
#             return redirect(
#                 "event_list"
#             )  # Redirect to the event list page after successful update
#         else:
#             return render(
#                 request,
#                 "events/update_event.html",
#                 {"form": form, "errors": form.errors},
#                 status=400,
#             )
#     else:
#         form = EventForm(instance=event)  # Pre-fill the form with the event data

#     return render(request, "events/update_event.html", {"form": form})


# def event_success(request):
#     return render(request, "events/event_success.html")


# @login_required  # Ensure only logged-in users can delete events
# def delete_event_view(request, event_id):
#     event = get_object_or_404(Event, id=event_id)

#     if request.method == "POST":
#         event.delete()
#         return redirect("event_list")  # Redirect to a success page after deletion

#     return render(request, "events/delete.html", {"event": event})


# @login_required
# def user_profile(request):
#     profile, created = UserProfile.objects.get_or_create(user=request.user)

#     if request.method == "POST":
#         form = UserProfileForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect("user_profile")
#     else:
#         form = UserProfileForm(instance=profile)

#     # Fetch the tickets for the current user
#     tickets = Ticket.objects.filter(user=request.user)

#     return render(
#         request, "events/user_profile.html", {"form": form, "tickets": tickets}
#     )


# @login_required
# def my_tickets(request):
#     tickets = Ticket.objects.filter(user=request.user)
#     return render(request, "events/my_tickets.html", {"tickets": tickets})


# @login_required
# def buy_tickets(request, event_id):
#     event = get_object_or_404(Event, id=event_id)

#     if request.method == "POST":
#         form = TicketPurchaseForm(request.POST)
#         if form.is_valid():
#             ticket = form.save(commit=False)
#             ticket.user = request.user
#             ticket.event = event
#             ticket.save()
#             messages.success(request, "Ticket purchased successfully!")
#             return redirect("user_profile")
#     else:
#         form = TicketPurchaseForm()

#     return render(request, "events/buy_tickets.html", {"event": event, "form": form})


# from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db.models import Q
from .models import UserProfile, Ticket, Event
from .forms import UserProfileForm
from django.shortcuts import render, get_object_or_404, redirect
from .forms import TicketPurchaseForm
from django.contrib import messages
import qrcode  # type: ignore
from django.http import JsonResponse
from io import BytesIO
import base64
from django.db.models import Sum
from django.contrib.auth.forms import AuthenticationForm
from .forms import EventForm

# @login_required
# def profile_tickets(request):
#     # Query all the events with tickets for the logged-in user
#     events_with_tickets = Ticket.objects.filter(user=request.user)

#     context = {
#         'events_with_tickets': events_with_tickets
#     }

#     return render(request, 'events\profile_tickets.html', context)


@login_required
def profile_tickets(request):
    # Group tickets by event and calculate the total tickets for each event
    events_with_tickets = (
        Ticket.objects.filter(user=request.user)
        .values("event__name", "event__id", "event__date_time")
        .annotate(total_tickets=Sum("quantity"))
    )

    return render(
        request,
        "events/profile_tickets.html",
        {"events_with_tickets": events_with_tickets},
    )


# Custom login view to handle both admin and user redirection
def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Check if the user is an admin or a regular user
            if user.is_staff or user.is_superuser:
                return redirect(
                    "event_list"
                )  # Admin is redirected to event_list (admin dashboard)
            else:
                return redirect("user_home")  # Regular user is redirected to user_home
    else:
        form = AuthenticationForm()

    return render(request, "events/login.html", {"form": form})


# Home page view to choose the user type
def home_page(request):
    return render(request, "events/homepage.html")


def generate_event_qr_code(request, event_id):
    user = request.user
    tickets = Ticket.objects.filter(user=user, event__id=event_id)

    if not tickets.exists():
        return JsonResponse({"error": "No tickets found for this event."}, status=404)

    # Prepare the QR code data
    qr_data = f"User: {user.username}\nEvent: {tickets.first().event.name}\nTotal Tickets: {tickets.aggregate(total_quantity=Sum('quantity'))['total_quantity']}"

    # Create the QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Save the image to a BytesIO stream
    img = qr.make_image(fill="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")

    # Convert the image to base64
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Return as JSON response
    return JsonResponse({"qr_code": img_str})


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
            user = form.save()
            login(request, user)
            return redirect("user_home")
    else:
        form = UserCreationForm()
    return render(request, "events/user_signup.html", {"form": form})


def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'events/signup.html')

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'events/signup.html')

        # If validations pass, create the user
        user = User.objects.create_user(username=username, password=password)
        login(request, user)  # Log the user in after signup
        return redirect('event_list')  # Redirect to the event list page

    return render(request, 'events/signup.html')


@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST)
        if form.is_valid():
            # Save the event with latitude and longitude included from the form
            form.save()
            return redirect(
                "event_list"
            )  # Redirect to the event list page after successful submission
    else:
        form = EventForm()

    return render(request, "events/create_event.html", {"form": form})


# def create_event(request):
#     if request.method == "POST":
#         form = EventForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect(
#                 "event_list"
#             )  # Redirect to the success page after form submission
#     else:
#         form = EventForm()
#     return render(request, "events/create_event.html", {"form": form})


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

    # Group tickets by event and calculate the total tickets for each event
    events_with_tickets = (
        Ticket.objects.filter(user=request.user)
        .values("event__name", "event__id")
        .annotate(total_tickets=Sum("quantity"))
    )

    return render(
        request,
        "events/user_profile.html",
        {"form": form, "events_with_tickets": events_with_tickets},
    )


# @login_required
# def user_profile(request):
#     profile, created = UserProfile.objects.get_or_create(user=request.user)

#     if request.method == "POST":
#         form = UserProfileForm(request.POST, instance=profile)
#         if form.is_valid():
#             form.save()
#             return redirect("user_profile")
#     else:
#         form = UserProfileForm(instance=profile)

#     # Fetch the tickets for the current user
#     tickets = Ticket.objects.filter(user=request.user)

#     return render(
#         request, "events/user_profile.html", {"form": form, "tickets": tickets}
#     )


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
            ticket.save()
            messages.success(request, "Ticket purchased successfully!")
            return redirect("user_profile")
    else:
        form = TicketPurchaseForm()

    return render(request, "events/buy_tickets.html", {"event": event, "form": form})
