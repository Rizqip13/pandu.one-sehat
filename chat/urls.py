from django.urls import path
from . import views

urlpatterns = [
    path("", views.chat_window, name="chat_window"),
    path("send/", views.send_message, name="send_message"),
    path("bot-response/", views.bot_response, name="bot_response"),
    path("stream/", views.chat_stream, name="chat_stream"),
    path("select-patient/", views.select_patient, name="select_patient"),
    path("new-session/", views.new_chat_session, name="new_chat_session"),
]