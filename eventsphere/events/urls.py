from django.urls import path
from .views import create_event
from .views import event_success
from .views import update_event_view


urlpatterns = [
    path('create/', create_event, name='create_event'),
    path('success/', event_success, name='event_success'),  # Define the success URL
    path('update/<int:event_id>/', update_event_view, name='update_event'),
]