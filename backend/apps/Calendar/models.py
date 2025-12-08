from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from apps.Users import models as user_model
from apps.Announcements import models as announcement_model  # if you really use it


class CalendarEventType(models.TextChoices):
    ACADEMIC = "acad", "Academic"
    ORGANIZATION = "org", "Organization"
    OFFICIAL = "official", "Official University"


class CalendarEntry(models.Model):
    # Generic link to the source object (event, announcement, etc.)
    source_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    source_id = models.PositiveIntegerField()
    source_object = GenericForeignKey("source_ct", "source_id")

    title = models.CharField(max_length=120)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=150, null=True, blank=True)

    is_public = models.BooleanField(default=True)
    tags = models.JSONField(default=list, blank=True)

    # Org events only
    org_status = models.CharField(max_length=10, blank=True)

    org_id = models.IntegerField(null=True, blank=True)
    section_id = models.IntegerField(null=True, blank=True)
    semester_id = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "calendar_entries"
        indexes = [
            models.Index(fields=["start_at"]),
            models.Index(fields=["end_at"]),
            models.Index(fields=["section_id"]),
            models.Index(fields=["semester_id"]),
            models.Index(fields=["org_id"]),
            models.Index(fields=["is_public"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["source_ct", "source_id", "start_at", "end_at"],
                name="unique_source_calendar_entry",
            )
        ]

    def __str__(self):
        return f"{self.title} ({self.start_at} – {self.end_at})"


class CalendarLogs(models.Model):
    event = models.ForeignKey(
        CalendarEntry, on_delete=models.CASCADE, related_name="logs"
    )
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "calendar_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"Log for {self.event.title} at {self.timestamp}"


class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "holidays"
        ordering = ["date"]
        indexes = [
            models.Index(fields=["date"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "date"], name="unique_holiday_per_date"
            )
        ]

    def __str__(self):
        return f"{self.name} on {self.date}"
