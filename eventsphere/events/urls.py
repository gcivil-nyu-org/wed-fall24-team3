from django.urls import path
from .views import create_event
from .views import event_success
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    path('create/', create_event, name='create_event'),
    path('success/', event_success, name='event_success'),
    path('login/', auth_views.LoginView.as_view(template_name='events/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('events/', views.event_list, name='event_list'),  # URL pattern for event list
    path('', views.home, name='home'),  # Define the success URL
]