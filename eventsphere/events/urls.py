from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    path('create/', views.create_event, name='create_event'),
    path('update/<int:event_id>/', views.update_event_view, name='update_event'),
    path('success/', views.event_success, name='event_success'),
    path('login/', auth_views.LoginView.as_view(template_name='events/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('events/', views.event_list, name='event_list'),  # URL pattern for event list
    path('', views.home, name='home'),  # Define the success URL
]