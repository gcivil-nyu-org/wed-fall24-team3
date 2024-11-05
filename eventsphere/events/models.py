from django.contrib.auth.models import User
from django.db import models


class CreatorProfile(models.Model):
    # creator_id = models.CharField(primary_key=True, max_length=10)
    creator = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    organisation = models.CharField(max_length=100, null=True, blank=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    interests = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.creator.username


class Event(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)  # This will be the address
    date_time = models.DateTimeField()
    schedule = models.TextField()
    speakers = models.CharField(max_length=500)
    category = models.CharField(max_length=100)  # Add this field for category
    image_url = models.URLField(
        blank=True, null=True
    )  # Add this field for S3 image link
    latitude = models.FloatField(null=True, blank=True)  # For latitude
    longitude = models.FloatField(null=True, blank=True)  # For longitude
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CreatorProfile, on_delete=models.CASCADE, null=True, blank=True
    )
    numTickets = models.IntegerField(null=True, blank=True)
    ticketsSold = models.IntegerField(default=0)
    
    @property
    def tickets_left(self):
        return (
            self.numTickets - self.ticketsSold
            if self.numTickets >= self.ticketsSold
            else 0
        )
    
    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    interests = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    
    def __str__(self):
        return self.user.username


class Ticket(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    email = models.EmailField(default="dummy@example.com")
    phone_number = models.CharField(default="999999999", max_length=12)
    quantity = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.event.name} - {self.user.username}"
