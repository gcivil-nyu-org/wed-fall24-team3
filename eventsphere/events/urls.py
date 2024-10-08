from django.urls import path
from .views import create_event
from .views import event_success


urlpatterns = [
    path('create/', create_event, name='create_event'),
    path('success/', event_success, name='event_success'),  # Define the success URL
]