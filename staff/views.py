from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from chat.models import ChatSession, Message


# Create your views here.
def staff_dashboard(request, session_id=None):
    chat_sessions = ChatSession.objects.filter(is_active=True).order_by("-created_at")

    if session_id:
        session = get_object_or_404(ChatSession, id=session_id)
    else:
        session = chat_sessions.first()

    messages = session.messages.order_by("timestamp") if session else []

    return render(
        request,
        "staff/dashboard.html",
        {
            "chat_sessions": chat_sessions,
            "session": session,
            "messages": messages,
        },
    )


def staff_file_list(request):
    return render(request, "staff/file_list.html")


@require_POST
def staff_toggle_takeover(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    session.taken_over_by_staff = not session.taken_over_by_staff
    session.save()
    return render(
        request, "staff/partials/take-over-btn.html", context={"session": session}
    )


@require_POST
def staff_send_message(request, session_id):
    session = ChatSession.objects.filter(id=session_id, is_active=True).first()

    if not session or not session.taken_over_by_staff:
        return HttpResponseForbidden("This chat is not available or not taken over.")

    content = request.POST.get("message", "").strip()
    if not content:
        return HttpResponse(status=400)  # Bad Request

    message = Message.objects.create(chat=session, sender="agent", content=content)

    html = render_to_string(
        "chat/partials/message_bubble.html",
        {"message": message, "session": session, "current_user_role": "agent"},
    )

    return HttpResponse(html)
