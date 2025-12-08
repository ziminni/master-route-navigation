from django.db import models
from apps.Users import models as user_models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from apps.Academics import models as academic_models
    
class DoW(models.TextChoices):
    MON = 'MON', 'Monday'
    TUE = 'TUE', 'Tuesday'
    WED = 'WED', 'Wednesday'
    THU = 'THU', 'Thursday'
    FRI = 'FRI', 'Friday'
    SAT = 'SAT', 'Saturday'
    SUN = 'SUN', 'Sunday'

# 1) Faculty declares recurring windows they CAN meet
#Needs the Semester for table for this
class AvailabilityRule(models.Model):
    faculty = models.ForeignKey(
        user_models.FacultyProfile, on_delete=models.CASCADE, related_name="availability_rules"
    )
    day_of_week = models.CharField(max_length=3, choices=DoW.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    # semester = models.ForeignKey(academic_models.Semester, on_delete=models.PROTECT, related_name="valid_time_span")
    semester = models.IntegerField()
    slot_minutes = models.PositiveSmallIntegerField(default=30)

    class Meta:
        indexes = [
            models.Index(fields=["faculty", "day_of_week"]),
        ]


# 2) Anything that blocks time (classes, org events, ad-hoc blocks, holidays)
# Needs to connect the calendar for this too
class BusyBlock(models.Model):
    faculty = models.ForeignKey(
        user_models.FacultyProfile, on_delete=models.CASCADE, related_name="busy_blocks"
    )
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    # Source from CalendarEntry / Holiday / other models
    source_ct = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.SET_NULL)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    source_object = GenericForeignKey("source_ct", "source_id")

    note = models.CharField(max_length=150, blank=True)
    class Meta:
        indexes = [
            models.Index(fields=["faculty", "start_at"]),
            models.Index(fields=["start_at", "end_at"]),
        ]



# 3) A student’s booking. Support split-times with child rows.
"""
    So,  Ive put a restriction on our appointment where it could only have one time slot instead of several time slot in one appointment so 
    we could like retain our past logic when it comes to this part.
"""
class Appointment(models.Model):

    PENDING = "pending"
    APPROVED = "approved"
    CANCELED = "canceled"
    COMPLETED = "completed"
    DENIED = "denied"

    STATUS = [
        (PENDING, "Pending"),
        (APPROVED, "Approved"),
        (CANCELED, "Canceled"),
        (COMPLETED, "Completed"),
        (DENIED, "Denied"),
    ]

    faculty = models.ForeignKey(
        user_models.FacultyProfile, on_delete=models.PROTECT, related_name="appointments"
    )
    student = models.ForeignKey(
        user_models.StudentProfile, on_delete=models.PROTECT, related_name="appointments"
    )

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    status = models.CharField(max_length=10, choices=STATUS, default=PENDING)
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["faculty", "status"]),
            models.Index(fields=["student"]),
            models.Index(fields=["start_at"]),
            models.Index(fields=["end_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_at__gt=models.F('start_at')),
                name='slot_end_after_start'
            )
        ]


