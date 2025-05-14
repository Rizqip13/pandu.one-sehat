import uuid

from django.db import models


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    taken_over_by_staff = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient_type} ({self.id})"


class Message(models.Model):
    SENDER_CHOICES = (
        ("patient", "Patient"),
        ("bot", "Bot"),
        ("agent", "Agent"),
        ("system", "System"),
    )

    chat = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}"
