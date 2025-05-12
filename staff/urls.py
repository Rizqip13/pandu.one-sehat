from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.staff_dashboard, name="staff_dashboard"),
    path("files/", views.staff_file_list, name="staff_file_list"),
]
