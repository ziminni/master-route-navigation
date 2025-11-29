from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
	list_display = (
		"id",
		"submission_type",
		"subject",
		"user",
		"is_anonymous",
		"resolved",
		"created_at",
	)
	list_filter = ("submission_type", "resolved", "is_anonymous", "created_at")
	search_fields = ("subject", "message", "user__username", "user__email")
	readonly_fields = ("created_at", "updated_at")
	ordering = ("-created_at",)

