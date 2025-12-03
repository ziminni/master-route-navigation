from django.contrib import admin
from .models import Message, Conversation

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "sender_name", "priority", "status", "department", "created_at")
    search_fields = ("subject", "content", "sender_name", "department")
    list_filter = ("priority", "status", "department", "created_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "creator", "created_at")
    search_fields = ("title", "creator__username")
    filter_horizontal = ("participants",)
