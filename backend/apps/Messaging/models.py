from django.db import models
from django.contrib.auth.models import User  # Assumed user model
# Create your models here.

class MessageThread(models.Model):
    subject = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject or f"Thread {self.id}"



class ThreadParticipant(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    #add roles if needed

    def __str__(self):
        return f"{self.user.username} in {self.thread}"

class Message(models.Model):
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message {self.id} by {self.sender.username}"
