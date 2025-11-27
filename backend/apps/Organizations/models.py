from django.db import models
from Users.models import BaseUser
from Users import models as user_models

# Create your models here.

class Status(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTICE = "inactive", "Inactive"

class OrganizationLevel(models.TextChoices):
    COLLEGE = "col", "College"
    PROGRAM = "prog", "Program"

class ApplicationStatus(models.TextChoices):
    ACCEPTED = "acc", "Accepted"
    REJECTED = "rej", "Rejected"
    PENDING = "pen", "Pending"


class Organization(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    status = models.CharField(
    max_length=7,
    choices= Status.choices,
    default= Status.ACTIVE

    )
    logo_path = models.CharField(max_length= 100)
    created_at = models.DateTimeField()
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

    class Meta:
        db_table = "organization "


class OrganizationMembers(models.Model):
    organization_id = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user_id = models.ForeignKey(BaseUser, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=7,
        choices=Status.choices,
        default=Status.ACTIVE
    )

    class Meta:
        db_table = "organization_members"


class OrganizationApplication(models.Model):
    user_id = models.ForeignKey(BaseUser)
    organization_id = models.ForeignKey(Organization)
    application_status = models.CharField(
    max_length= 3,
    choices=ApplicationStatus.choices,
    default=ApplicationStatus.PENDING
    )

    class Meta:
        db_table = "organization_application"


class ApplicationDetails(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()

    class Meta:
        db_table = "application_details"


class Positions(models.Model):
    name = models.CharField( max_length=50)
    description = models.TextField()

    class Meta:
        db_table = "positions"

class OrgAdviserTerm(models.Model):
    class AdviserRoles(models.TextChoices):
        PRIMARY = "pri","Primary"
        SECONDARY = "sec", "Secondary"
    
    adviser_id = models.ForeignKey(user_models.FacultyProfile, on_delete=models.PROTECT, related_name="org_advisory")
    role = models.CharField(max_length = 12, choices=AdviserRoles.choices)
    semester = models.IntegerField() #Semester key
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            
        ]


class Officers(models.Model):
    position_id = models.ForeignKey(Positions)
    org_member_id = models.ForeignKey(OrganizationMembers)
    start_term = models.DateTimeField()
    end_term = models.DateTimeField()
    status = models.CharField(
    max_length=7,
    choices=Status.choices
    )
    updated_by = models.ForeignKey(BaseUser)
    class Meta:
        db_table = "officers"
