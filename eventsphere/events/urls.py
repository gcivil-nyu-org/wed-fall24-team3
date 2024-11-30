from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .views import user_profile, my_tickets, map_view

urlpatterns = [
    path(
        "generate_event_qr/<int:event_id>/",
        views.generate_event_qr_code,
        name="generate_event_qr",
    ),
    path('toggle_favorite/<int:event_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('profile/chats/', views.profile_chats, name='profile_chats'),  # Add this line
    # Favorites List View
    path('profile/favorites/', views.profile_favorites, name='profile_favorites'),  # Use this as the main route for the favorites tab
    # path('toggle_favorite/<int:event_id>/', views.toggle_favorite, name='toggle_favorite'),
    # path('profile/favorites/', views.favorites_list, name='favorites_list'),
    # path('profile/favorites/', views.profile_favorites, name='profile_favorites'),
    path("profile/tickets/", views.profile_tickets, name="profile_tickets"),
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
    path(
        "creator/", views.creator_dashboard, name="creator_dashboard"
    ),  # creator dashboard url
    path(
        "fetch_filter_wise_data/",
        views.fetch_filter_wise_data,
        name="fetch_filter_wise_data",
    ),
    path("creatorprofile/", views.creator_profile, name="creator_profile"),
    path("event/<int:event_id>/join_chat/", views.join_chat, name="join_chat"),
    path("chat_room/<int:room_id>/", views.chat_room, name="chat_room"),
    path(
        "chat_room/<int:room_id>/send_message/", views.send_message, name="send_message"
    ),
    path(
        "chat_room/<int:room_id>/make_announcement/",
        views.make_announcement,
        name="make_announcement",
    ),
    path(
        "chat_room/<int:room_id>/kick_member/<int:user_id>/",
        views.kick_member,
        name="kick_member",
    ),
    path("chat_room/<int:room_id>/leave/", views.leave_chat, name="leave_chat"),
    path("not-authorized/", views.not_authorized, name="not_authorized"),
    path("notifications", views.view_notifications, name="notifications"),
    path(
        "notifications/mark_as_read/<int:notification_id>/",
        views.mark_as_read,
        name="mark_as_read",
    ),
    path(
        "notifications/mark_all_as_read",
        views.mark_all_as_read,
        name="mark_all_as_read",
    ),
    path(
        "notifications/get_unread_notif",
        views.get_user_unread_notifications,
        name="get_user_unread_notifications",
    ),
    path("mapview/", map_view, name="map_view"),  # Map View
]
