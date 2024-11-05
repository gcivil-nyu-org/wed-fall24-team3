import base64
import qrcode  # type: ignore
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from .forms import UserProfileForm, CreatorProfileForm, TicketPurchaseForm, EventForm
from .models import UserProfile, CreatorProfile, Ticket, Event
from io import BytesIO
import boto3
from botocore.exceptions import BotoCoreError, ClientError


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
            if user.is_superuser:
                return redirect(
                    "event_list"
                )  # Admin is redirected to event_list (admin dashboard)
            elif CreatorProfile.objects.filter(creator=request.user).exists():
                return redirect("creator_dashboard")
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
            user = form.save()
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
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        user_type = request.POST.get("user_type")

        # Check if passwords match
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "events/signup.html")

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, "events/signup.html")

        # Ensure a user type was selected
        if not user_type:
            messages.error(request, "Please select an account type.")
            return render(request, "events/signup.html")

        # If validations pass, create the user
        user = User.objects.create_user(username=username, password=password)
        if user_type == "admin":
            user.is_superuser = True
            user.save()
            login(request, user)
            return redirect("event_list")

        elif user_type == "creator":
            user.is_staff = True
            user.save()
            CreatorProfile.objects.create(creator=user)
            login(request, user)
            return redirect("creator_profile")

        else:
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect("user_profile")

    return render(request, "events/signup.html")


@login_required
def create_event(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            image = request.FILES.get("image")
            event.created_by = request.user.creatorprofile

            if image:
                # Upload the image to S3
                s3 = boto3.client("s3")
                bucket_name = "eventsphere-images"
                image_key = f"events/{image.name}"

                # Upload the file
                s3.upload_fileobj(
                    image,
                    bucket_name,
                    image_key,
                    ExtraArgs={"ContentType": image.content_type},
                )

                # Get the image URL
                event.image_url = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"

            event.save()
            messages.success(request, "Event created successfully!")
            if request.user.is_superuser:
                return redirect("event_list")
            return redirect("creator_dashboard")
    else:
        form = EventForm()

    return render(request, "events/create_event.html", {"form": form})


def update_event_view(request, event_id):
    # Fetch the event by its ID and store initial location, latitude, and longitude
    event = get_object_or_404(Event, id=event_id)
    initial_location = event.location
    initial_latitude = event.latitude
    initial_longitude = event.longitude

    if request.method == "POST":
        # Initialize the form with POST data, uploaded files, and the existing event instance
        form = EventForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            # Save form data excluding image and coordinates
            event = form.save(commit=False)

            # Check if location has changed
            if form.cleaned_data.get("location") == initial_location:
                # If location is unchanged, retain the original latitude and longitude
                event.latitude = initial_latitude
                event.longitude = initial_longitude
            else:
                # Optional: Logic to update latitude and longitude based on the new location, if needed
                # Example: event.latitude, event.longitude = get_coordinates_from_location(event.location)
                pass

            # Handle image upload if a new image is uploaded
            image = request.FILES.get("image")
            if image:
                try:
                    # Initialize S3 client
                    s3 = boto3.client("s3")

                    # Define S3 bucket and object key
                    bucket_name = "eventsphere-images"
                    image_key = f"events/{image.name}"

                    # Upload the file
                    s3.upload_fileobj(
                        image,
                        bucket_name,
                        image_key,
                        ExtraArgs={"ContentType": image.content_type},
                    )

                    # Set the image URL
                    event.image_url = (
                        f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
                    )

                except (BotoCoreError, ClientError) as e:
                    # Log or handle the exception as needed
                    print(f"Error uploading to S3: {e}")
                    return render(
                        request,
                        "events/update_event.html",
                        {
                            "form": form,
                            "errors": ["Failed to upload image. Please try again."],
                        },
                    )

            # Save the event instance to the database
            event.save()

            # Redirect based on user type
            if request.user.is_superuser:
                return redirect("event_list")
            return redirect("creator_dashboard")

        else:
            # Render the form with validation errors if form is invalid
            return render(
                request,
                "events/update_event.html",
                {"form": form, "errors": form.errors},
                status=400,
            )

    else:
        # GET request, render the form with the existing event instance
        form = EventForm(instance=event)

    # Render the form with GET request or any encountered errors
    return render(request, "events/update_event.html", {"form": form})


def event_success(request):
    return render(request, "events/event_success.html")


@login_required  # Ensure only logged-in users can delete events
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        event.delete()
        if request.user.is_superuser:
            return redirect("event_list")  # Redirect to a success page after deletion
        else:
            return redirect("creator_dashboard")

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

            if ticket.quantity > event.tickets_left:
                messages.error(request, "Not enough tickets available!")
                return render(
                    request, "events/buy_tickets.html", {"event": event, "form": form}
                )

            # Save the ticket
            ticket.save()

            # Update the event's ticketsSold
            event.ticketsSold += ticket.quantity
            event.save(update_fields=["ticketsSold"])

            messages.success(request, "Ticket purchased successfully!")
            return redirect("user_profile")

    else:
        form = TicketPurchaseForm()

    return render(request, "events/buy_tickets.html", {"event": event, "form": form})
