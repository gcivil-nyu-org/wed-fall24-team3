from django.contrib.auth import views as auth_views
from django.urls import path
from .views import user_profile, my_tickets
from . import views

urlpatterns = [
    path(
        "generate_event_qr/<int:event_id>/",
        views.generate_event_qr_code,
        name="generate_event_qr",
    ),
    path('profile/tickets/', views.profile_tickets, name='profile_tickets'),
    path("create/", views.create_event, name="create_event"),
    path("update/<int:event_id>/", views.update_event_view, name="update_event"),
    path("delete/<int:event_id>/", views.delete_event_view, name="delete_event"),
    path("success/", views.event_success, name="event_success"),
    # path(
    #     "login/",
    #     auth_views.LoginView.as_view(template_name="events/login.html"),
    #     name="login",
    # ),
    path("login/", views.login_view, name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    path("signup/", views.signup, name="signup"),
    path("events/", views.event_list, name="event_list"),
    path("home/", views.home, name="home"),  # URL pattern for event list
    path("", views.home_page, name="homepage"),
    path("userhome/", views.user_home, name="user_home"),
    path("userevents/", views.user_event_list, name="user_event_list"),
    path("userevents/<int:pk>/", views.event_detail, name="event_detail"),
    path("profile/", user_profile, name="user_profile"),
    path("my_tickets/", my_tickets, name="my_tickets"),
    path("events/<int:event_id>/buy-tickets/", views.buy_tickets, name="buy_tickets"),
    # Authentication URLs
    path(
        "userlogin/",
        auth_views.LoginView.as_view(template_name="events/user_login.html"),
        name="user_login",
    ),
    path(
        "userlogout/",
        auth_views.LogoutView.as_view(next_page="user_login"),
        name="user_logout",
    ),
    path(
        "usersignup/", views.user_signup, name="user_signup"
    ),  # Define the success URL
]
