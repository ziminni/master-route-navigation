from django.conf import settings
from django.db import models


class Feedback(models.Model):
	"""Stores a single feedback / suggestion / complaint entry.

	Fields mirror the frontend FeedbackBox: a submission type, subject,
	message body, optional submitting user, and timestamps.
	"""

	TYPE_SUGGESTION = "suggestion"
	TYPE_COMPLAINT = "complaint"
	TYPE_FEEDBACK = "feedback"

	TYPE_CHOICES = [
		(TYPE_SUGGESTION, "Suggestion"),
		(TYPE_COMPLAINT, "Complaint"),
		(TYPE_FEEDBACK, "Feedback"),
	]

	submission_type = models.CharField(
		max_length=32, choices=TYPE_CHOICES, default=TYPE_FEEDBACK, db_index=True
	)
	subject = models.CharField(max_length=255, blank=True)
	message = models.TextField()
	user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.SET_NULL,
		related_name="feedback_entries",
	)
	is_anonymous = models.BooleanField(
		default=False,
		help_text="If true, the entry should be treated as submitted anonymously",
	)
	resolved = models.BooleanField(default=False)
	admin_response = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ["-created_at"]
		verbose_name = "Feedback"
		verbose_name_plural = "Feedback"

	def __str__(self) -> str:
		subject = self.subject or (self.message[:50] + ("..." if len(self.message) > 50 else ""))
		return f"{self.get_submission_type_display()} - {subject}"

	def short_message(self, length: int = 75) -> str:
		if not self.message:
			return ""
		return self.message if len(self.message) <= length else self.message[: length - 3] + "..."

