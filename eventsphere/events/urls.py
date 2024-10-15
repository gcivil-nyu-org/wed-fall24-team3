from django.urls import path
from .views import create_event
from .views import event_success
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    path('create/', views.create_event, name='create_event'),
    path('update/<int:event_id>/', views.update_event_view, name='update_event'),
    path('delete/<int:event_id>/', views.delete_event_view, name='delete_event'),
    path('success/', views.event_success, name='event_success'),
    path('login/', auth_views.LoginView.as_view(template_name='events/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('events/', views.event_list, name='event_list'),  # URL pattern for event list
    path('', views.home, name='home'),
      
    path('userhome/', views.user_home, name='user_home'),
    path('userevents/', views.user_event_list, name='user_event_list'),
    path('userevents/<int:pk>/', views.event_detail, name='event_detail'),

    # Authentication URLs
    path('userlogin/', auth_views.LoginView.as_view(template_name='events/user_login.html'), name='user_login'),
    path('userlogout/', auth_views.LogoutView.as_view(next_page='user_home'), name='user_logout'),
    path('usersignup/', views.user_signup, name='user_signup')  # Define the success URL
]