from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Conversation(models.Model):
    CONVERSATION_TYPES = [
        ("direct", "Direct"),   # one-on-one
        ("group", "Group"),
    ]

    title = models.CharField(max_length=255, blank=True)
    creator = models.ForeignKey(User, related_name="created_conversations",
                                on_delete=models.CASCADE)
    participants = models.ManyToManyField(User, related_name="conversations", blank=True)
    type = models.CharField(max_length=10, choices=CONVERSATION_TYPES, default="direct")
    group_name = models.CharField(max_length=255, blank=True)  # for group display
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.type == "group" and self.group_name:
            return self.group_name
        return self.title or f"Conversation {self.id}"


class ConversationHide(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hidden_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("conversation", "user")


class Message(models.Model):
    PRIORITY_CHOICES = [
        ("urgent", "Urgent"),
        ("high", "High"),
        ("normal", "Normal"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("resolved", "Resolved"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(
        User,
        related_name="sent_messages",
        on_delete=models.CASCADE,
    )

    receiver = models.ForeignKey(
        User,
        related_name="received_messages",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    subject = models.CharField(max_length=255)
    content = models.TextField()

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default="normal",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
    )
    attachment = models.FileField(
        upload_to="message_attachments/",
        null=True,
        blank=True,
    )
    department = models.CharField(max_length=100, default="General")
    message_type = models.CharField(max_length=50, default="normal")
    is_broadcast = models.BooleanField(default=False)

    sender_name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.sender_name and self.sender:
            self.sender_name = (
                    self.sender.get_full_name() or self.sender.get_username()
            )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subject} ({self.sender_name})"
