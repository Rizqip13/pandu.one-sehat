from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("dashboard/<uuid:session_id>/", views.staff_dashboard, name="staff_dashboard"),
    path("files/", views.staff_file_list, name="staff_file_list"),
    path(
        "chat/<uuid:session_id>/toggle-takeover/",
        views.staff_toggle_takeover,
        name="staff_toggle_takeover",
    ),
    path(
        "chat/<uuid:session_id>/send/",
        views.staff_send_message,
        name="staff_send_message",
    ),
]
