from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse
from .models import ChatSession, Message
from .profiles import PATIENT_PROFILES
import time
from django.template.loader import render_to_string
from django.http import HttpResponse
import google.api_core.exceptions

from .rag_agent import rag_agent


def generate_bot_reply(user_input, chat_session=None):
    if not rag_agent:
        return {
            "sender": "system",
            "content": "⚠️ Our AI system is currently unavailable. Please try again later."
        }

    try:
        reply_text = rag_agent.chat(user_input, chat_session=chat_session)
        return {
            "sender": "bot",
            "content": reply_text
        }

    except google.api_core.exceptions.ResourceExhausted:
        return {
            "sender": "system",
            "content": "⚠️ Our AI system has reached its daily usage limit. Please try again tomorrow or contact a support agent."
        }

    except Exception as e:
        print("[Gemini Error]", e)
        return {
            "sender": "system",
            "content": "❌ An unexpected error occurred while processing your request. Please try again in a moment or contact support."
        }

# Mock patient selection (Login)
def select_patient(request):
    if request.method == "POST":
        patient_type = request.POST.get("patient_type")
        request.session["patient_type"] = patient_type
        request.session.pop("chat_session_id", None)
        return redirect("chat_window")
    
    return render(request, "chat/select_patient.html")

@require_GET
def bot_response(request):
    session = ChatSession.objects.get(id=request.session["chat_session_id"])
    last_patient_message = session.messages.filter(sender="patient").latest("timestamp")

    reply = generate_bot_reply(last_patient_message.content, chat_session=session)
    bot_message = Message.objects.create(chat=session, sender=reply["sender"], content=reply["content"])

    html = render_to_string("chat/partials/message_bubble.html", {"message": bot_message, "session": session})
    return HttpResponse(html)

# Main chat window
def chat_window(request):
    patient_type = request.session.get("patient_type")

    if not patient_type:
        return redirect("select_patient")

    if not request.session.get("chat_session_id"):
        # Try to find an existing active session
        existing_session = ChatSession.objects.filter(patient_id=patient_type, is_active=True).last()
        
        if existing_session:
            session = existing_session
        else:
            session = ChatSession.objects.create(patient_id=patient_type)
        
        request.session["chat_session_id"] = str(session.id)
    else:
        try:
            session = ChatSession.objects.get(id=request.session["chat_session_id"])
        except ChatSession.DoesNotExist:
            # Fallback if session ID in session is broken
            session = ChatSession.objects.create(patient_id=patient_type)
            request.session["chat_session_id"] = str(session.id)

    messages = session.messages.order_by("timestamp")
    return render(request, "chat/chat_window.html", {"session": session, "messages": messages, "current_user_role": "patient"})

# Sending a message
def send_message(request):
    if request.method == "POST":
        content = request.POST.get("content")
        chat_id = request.session.get("chat_session_id")
        session = ChatSession.objects.get(id=chat_id)

        # Save patient message
        patient_message = Message.objects.create(
            chat=session,
            sender="patient",
            content=content
        )

        # Render both messages to the chat box
        patient_bubble = render_to_string("chat/partials/message_bubble.html", {"message": patient_message, "session": session, "current_user_role": "patient"})
        typing_bubble = render_to_string("chat/partials/bot_typing.html")

        return HttpResponse(patient_bubble + typing_bubble)


# Server-Sent Events Stream
def chat_stream(request):
    session = ChatSession.objects.get(id=request.session["chat_session_id"])

    def event_stream():
        last_id = request.GET.get("last_id", None)
        while True:
            if last_id:
                new_messages = session.messages.filter(id__gt=last_id).order_by("timestamp")
            else:
                new_messages = session.messages.all().order_by("timestamp")

            if new_messages.exists():
                for msg in new_messages:
                    yield f"data: {msg.sender}:{msg.content}\\n\\n"
                    last_id = msg.id
            time.sleep(2)

    response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    return response

def new_chat_session(request):
    patient_type = request.session.get("patient_type")

    if not patient_type:
        return redirect("select_patient")

    # Create fresh session
    session = ChatSession.objects.create(patient_id=patient_type)
    request.session["chat_session_id"] = str(session.id)
    
    return redirect("chat_window")
