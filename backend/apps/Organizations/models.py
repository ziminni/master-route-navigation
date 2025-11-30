from django.db import models
from django.db.models import Q, F
from apps.Users.models import StudentProfile, FacultyProfile

# Create your models here.

class Semester(models.Model):
    sem = models.SmallIntegerField()

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

    # class Meta:
    #     db_table = "organization"


class OrganizationMembers(models.Model):
    organization_id = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user_id = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    joined_at = models.DateField(auto_now_add=True)

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
    semester = models.IntegerField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    class Meta:
        constraints = [
            # only one PRIMARY adviser per org per semester
            models.UniqueConstraint(
                fields=["org", "semester", "role"],
                name="one_primary_adviser_per_semester",
                condition=models.Q(role="pri"),
            ),
            # prevent duplicate same adviser/role/period rows
            models.UniqueConstraint(
                fields=["org","adviser","semester","role"], 
                name="uniq_adviser_role_period"
            ),
        ]



class OfficerTerm(models.Model):
    org          = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="officer_terms")
    position     = models.ForeignKey(Positions, on_delete=models.PROTECT, related_name="terms")
    member       = models.ForeignKey(OrganizationMembers, on_delete=models.CASCADE, related_name="officer_terms")
    start_term   = models.DateField()
    end_term     = models.DateField(null=True, blank=True)
    status       = models.CharField(max_length=10, choices=[("active","Active"), ("inactive","Inactive")], default="active")
    updated_by   = models.ForeignKey(StudentProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
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


class OrgActivation(models.Model):
    org       = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="activations")
    semester  = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="org_activations")
    status    = models.CharField(max_length=10, choices=[("active","Active"), ("inactive","Inactive")], default="active")
    registered_at = models.DateTimeField(auto_now_add=True)
    notes     = models.TextField(blank=True)

    class Meta:
        constraints = [
            # at most one activation row per (org, semester)
            models.UniqueConstraint(fields=["org", "semester"], name="uniq_org_semester_activation"),
            # optional: only one *active* row per (org, semester)
            models.UniqueConstraint(fields=["org", "semester", "status"],
                                    name="one_active_activation_per_period",
                                    condition=models.Q(status="active")),
        ]
