from django.db import models
from django.db.models import Q, F
from django.conf import settings
from apps.Users.models import StudentProfile, FacultyProfile

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
    # program_id = models.ForeignKey() needs program table
    
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


