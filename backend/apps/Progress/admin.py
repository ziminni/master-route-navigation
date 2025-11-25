from django.contrib import admin
from .models import FacultyFeedbackMessage

@admin.register(FacultyFeedbackMessage)
class FacultyFeedbackMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "faculty", "student", "grade", "date_sent", "status")
    list_filter = ("status", "date_sent", "faculty")
    search_fields = ("message", "student__username", "faculty__username")
    ordering = ("-date_sent",)