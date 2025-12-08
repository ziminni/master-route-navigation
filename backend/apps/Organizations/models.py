from django.db import models
from django.db.models import Q, F
from django.conf import settings
from apps.Users.models import StudentProfile, FacultyProfile
from apps.Users import models as user_model
from apps.Academics import models as acad_model

# Create your models here.

class Status(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"

class ApplicationStatus(models.TextChoices):
    ACCEPTED = "acc", "Accepted"
    REJECTED = "rej", "Rejected"
    PENDING = "pen", "Pending"


class Organization(models.Model):
    
    class OrganizationLevel(models.TextChoices):
        COLLEGE = "col", "College"
        PROGRAM = "prog", "Program"

    name = models.CharField(max_length=150)
    description = models.TextField()
    objectives = models.TextField(default="", blank=True)
    status = models.CharField(
    max_length=10,
    choices= Status.choices,
    default= Status.ACTIVE

    )
    logo_path = models.FileField(upload_to='logo/')
    created_at = models.DateTimeField(auto_now_add=True)
    
    org_level = models.CharField(
    max_length= 7,
    choices=OrganizationLevel.choices
    )

    main_org = models.ManyToManyField(
    "self",
    symmetrical=False,
    blank=True
    )
    
    is_archived = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # class Meta:
    #     db_table = "organization"

# MODULE 6
class EventType(models.Model):
    # primary id is still automated
    #Must make sure that it has both behavioral and competitive values
    event_type = models.CharField(max_length=50)
    class Meta:
        db_table = "event_types"

class Log(models.Model):
    user_id = models.SmallIntegerField()
    class Action(models.TextChoices):
        KICKED = "kicked", "Kicked"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        APPLIED = "applied", "Applied"
        ARCHIVED = "archived", "Archived"
        EDITED = "edited", "Edited"
        CREATED = "created", "Created"
        ACTIVATE = "activated", "Activated"
        DEACTIVATE = "deactivate", 'Deactivate'
    
    action = models.CharField(
        max_length= 20,
        choices=Action.choices,

    )
    
    target_id = models.SmallIntegerField()
    
    target_type = models.CharField(max_length=100)
    
    date_created = models.DateTimeField(auto_now_add=True)
        
         


class OrganizationMembers(models.Model):
    organization_id = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user_id = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    joined_at = models.DateField(auto_now_add=True)
    is_kick = models.BooleanField(default=False)
    kicked_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="kicked_members")

    class Meta:
        # db_table = "organization_members"
        unique_together = [("organization_id", "user_id")]  


class ApplicationDetails(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()

    # class Meta:
    #     db_table = "application_details"

class MembershipApplication(models.Model):
    user_id = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    application_details_id = models.ForeignKey(ApplicationDetails, on_delete=models.PROTECT)
    organization_id = models.ForeignKey(Organization, on_delete=models.CASCADE)
    application_status = models.CharField(
    max_length= 3,
    choices=ApplicationStatus.choices,
    default=ApplicationStatus.PENDING
    )

    # class Meta:
    #     db_table = "membership_application"

class Positions(models.Model):
    name = models.CharField( max_length=50)
    rank = models.PositiveSmallIntegerField(default=100)
    description = models.TextField()

    # class Meta:
    #     db_table = "positions"

class OrgAdviserTerm(models.Model):
    class AdviserRoles(models.TextChoices):
        PRIMARY = "pri","Primary"
        SECONDARY = "sec", "Secondary"
    
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    adviser = models.ForeignKey(FacultyProfile, on_delete=models.PROTECT, related_name="org_advisory")
    role = models.CharField(max_length=12, choices=AdviserRoles.choices)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    class Meta:
        constraints = [
            # only one PRIMARY adviser per org per 
            models.UniqueConstraint(
                fields=["org", "role"],
                name="one_primary_adviser",
                condition=models.Q(role="pri"),
            ),
            # prevent duplicate same adviser/role/period rows
            models.UniqueConstraint(
                fields=["org","adviser","role"], 
                name="uniq_adviser_role_period"
            ),
        ]


class OfficerTerm(models.Model):
    org          = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="officer_terms")
    position     = models.ForeignKey(Positions, on_delete=models.PROTECT, related_name="terms")
    member       = models.ForeignKey(OrganizationMembers, on_delete=models.CASCADE, related_name="officer_terms")
    start_term   = models.DateField()
    end_term     = models.DateField()
    status       = models.CharField(max_length=10, choices=[("active","Active"), ("inactive","Inactive")], default="active")
    photo        = models.ImageField(upload_to='officer_photos/', null=True, blank=True)
    updated_by   = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # date sanity
            models.CheckConstraint(check=Q(start_term__lt=F("end_term")) | Q(end_term__isnull=True), name="officer_term_order"),
            # one active officer per (org, position)
            models.UniqueConstraint(
                fields=["org", "position", "status"],
                condition=Q(status="active"),
                name="one_active_officer_per_position",
            ),
            # member must belong to same org (achieved by FK chain; member.org == org)
        ]

# MODULE 6
class EventSchedule(models.Model):
    # The event as a whole is pretty much the EventScheduleBlock
    # This is because the event may go on at an irregular scheduling
    # I just realized this should be connected to the events if that's the case O_O, this is now fixed here.
    # It is now linked to the Event instead of the EventScheduleBlock
    event_schedule_block_id = models.ForeignKey('EventScheduleBlock', on_delete=models.PROTECT)
    # As usual, the ID is omitted
    event_id = models.ForeignKey('Event', on_delete=models.PROTECT)
    # Perfect example of lazy loading. Because the Event is defined later, we can't just reference it normally. This
    # makes django look up the model later.
    # IMPORTANT:  the syntax for referencing models from different files is
    # 'app_name.ModelName'.the app_name is always the one in the apps.py
    user_id = models.ForeignKey('users.StudentProfile', on_delete=models.PROTECT)
    # When it's from another app (in this context, users) and we want to implement lazy loading...
    # use the label, not the full app name
    start_time = models.TimeField()
    end_time = models.TimeField()
    creation_date = models.DateTimeField()  # This is when the event was crated


# MODULE 6
class Event(models.Model):
    # It had an issue in database diagram where event_schedule_block_id had the event_id instead of the other way around
    # Event ID already done over
    # org_id = models.ForeignKey(user_model.BaseUser, on_delete=models.CASCADE) I need an organization model first
    # You know, consider moving this to Event Schedule Block
    # Daily reminder that models.PROTECT pretty much prevents deletion of an organization if this exists.
    event_schedule_block = models.ForeignKey('EventScheduleBlock', on_delete=models.PROTECT)
    event_type = models.ForeignKey('EventType', on_delete=models.PROTECT)
    # Commented out since Semester model don't exist yet
    sem_id = models.ForeignKey('Academics.Semester',on_delete=models.PROTECT)

    title = models.CharField(max_length=50)
    venue = models.CharField(max_length=100)

    class EventStatus(models.TextChoices):
        # max length is 5 for the codes, should still be recognizable like a mnemonic
        proposed = "prpsd", "proposed"
        approved = "aprvd", "approved"
        completed = "cmplt", "completed"
        rescheduled = "resch", "rescheduled"

    event_status = models.CharField(
        max_length=5,
        choices=EventStatus.choices,
        default=EventStatus.proposed
    )


# MODULE 6
class EventScheduleBlock(models.Model):
    name = models.CharField(max_length=100)  # Name for this schedule block group
    description = models.TextField(blank=True)  # Optional description
    
    class Meta:
        db_table = "event_schedule_blocks"


# MODULE 6
class EventAttendance(models.Model):
    # ID predeterminated
    event_id = models.ForeignKey(Event, on_delete=models.PROTECT)
    student_id = models.ForeignKey(user_model.StudentProfile, on_delete=models.PROTECT)
    # Never use BaseUser for such kak
    time_in = models.DateTimeField()
    time_out = models.DateTimeField()
    notes = models.CharField(max_length=100)
    class Meta:
        db_table = "event_attendance"


# MODULE 6
class EventApproval(models.Model):
    # ID included
    event_id = models.ForeignKey('Event', on_delete=models.PROTECT)
    approver_id = models.ForeignKey(user_model.FacultyProfile, on_delete=models.PROTECT)
    approved_at = models.DateTimeField(auto_now_add=True)
    notes = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "event_approvals"
        constraints = [
            models.UniqueConstraint(
                fields=['event_id'],
                name="events_approved_only_once"
                #This ensures event approvals only happen once
            )
        ]
