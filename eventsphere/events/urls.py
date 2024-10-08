from django.urls import path
from . import views

urlpatterns = [
    path('<str:username>/', views.user_profile_view, name='user_profile'),  # Add this line for profile
]