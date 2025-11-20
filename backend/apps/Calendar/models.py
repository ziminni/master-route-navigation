from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

# Create your models here.
from backend.apps.Users import models as user_model
from backend.apps.Announcements import models as announcement_model

class CalendarEventType(models.TextChoices):
    ACADEMIC = 'acad', 'Academic'
    ORGANIZATION = 'org', 'Organization'
    OFFICIAL = 'official', 'Official University'

class CalendarEntry(models.Model):

    source_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    source_id = models.PositiveIntegerField()
    source_object = GenericForeignKey('source_ct', 'source_id')

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
        index = [
            models.Index(fields=['start_at']),
            models.Index(fields=['end_at']),
            models.Index(fields=['section_id']),
            models.Index(fields=['semester_id']),
            models.Index(fields=['org_id']),
            models.Index(fields=['is_public']),
        ]
        constraint = [
            models.UniqueConstraint(
                fields=['source_ct', 'source_id','start_at','end_at'],
                name='unique_source_calendar_entry'
            )
        ]


# class CalendarEntry(models.Model):
#     title = models.CharField(max_length=120)
#     description = models.TextField(null=True, blank=True)
#     created_by = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT, related_name="created_events")
#     event_type = models.CharField(
#         max_length=10,
#         choices=CalendarEventType.choices,
#         default=CalendarEventType.ACADEMIC
#     )
#     start_datetime = models.DateTimeField()
#     end_datetime = models.DateTimeField()
#     location = models.CharField(max_length=150, null=True, blank=True)
#     is_public = models.BooleanField(default=True)
#     is_official = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_by = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "calendar_entries"
#         ordering = ['start_datetime']
#         indexes = [
#             models.Index(fields=['event_type']),
#             models.Index(fields=['start_datetime', 'end_datetime']),
#         ]
#         constraints = [
#             models.CheckConstraint(
#                 check=models.Q(end_datetime__gt=models.F('start_datetime')),
#                 name='end_after_start'
#             ),
#         ]

#     def __str__(self):
#         return f"{self.title} ({self.start_datetime.date()})"

class CalendarLogs(models.Model):
    event = models.ForeignKey(CalendarEvent, on_delete=models.CASCADE, related_name="logs")
    action = models.CharField(max_length=50)
    performed_by = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "calendar_logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
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
        ordering = ['date']
        indexes = [
            models.Index(fields=['date']),
        ]
        constraints = [
            models.UniqueConstraint(fields=['name', 'date'], name='unique_holiday_per_date')
        ]

    def __str__(self):
        return f"{self.name} on {self.date}"