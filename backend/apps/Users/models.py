from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.

# ID are auto generate by Django
class FacultyDepartment(models.Model):
    department_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.department_name

class Position(models.Model):
    position_name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.position_name

class Program(models.Model):
    program_name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.program_name

class Section(models.Model):
    section_name = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.section_name

import uuid
def user_avatar_upload_to(instance, filename):
    ext = filename.split('.')[-1].lower()
    return f"profile_pics/users/{instance.pk}/avatar-{uuid.uuid4().hex[:8]}.{ext}"

class BaseUser(AbstractUser):
    """Custom model that would inherit and extend the AbstractBaseUser"""
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    suffix = models.CharField(max_length=5, blank=True, null=True)
    profile_picture = models.ImageField(upload_to="profile_pics/", blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    institutional_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("student", "Student"),
        ("faculty", "Faculty"),
        ("staff", "Staff"),
    ]
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)

class FacultyProfile(models.Model):
    user               = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="faculty_profile")
    faculty_department = models.ForeignKey(FacultyDepartment, on_delete=models.SET_NULL, null=True)
    position           = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    hire_date          = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"FacultyProfile<{self.user_id}>"
    

class StudentProfile(models.Model):
    user         = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    program      = models.ForeignKey(Program, on_delete=models.SET_NULL, null=True)
    section      = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True)
    indiv_points = models.IntegerField(default=0)
    year_level   = models.IntegerField()

    def __str__(self):
        return f"StudentProfile<{self.user_id}>"


class StaffProfile(models.Model):
    user               = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staff_profile")
    faculty_department = models.ForeignKey(FacultyDepartment, on_delete=models.SET_NULL, null=True)
    job_title          = models.CharField(max_length=50)

    def __str__(self):
        return f"StaffProfile<{self.user_id}>"


# simple models for resume builder functionality
class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class Education(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_educations")
    degree = models.CharField(max_length=200, blank=True)
    school = models.CharField(max_length=200)
    city = models.CharField(max_length=120, blank=True)
    start_month = models.CharField(max_length=20, blank=True)
    start_year = models.CharField(max_length=4, blank=True)
    end_month = models.CharField(max_length=20, blank=True)
    end_year = models.CharField(max_length=4, blank=True)
    description = models.TextField(blank=True)

class Experience(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_experiences")
    job_title = models.CharField(max_length=200)
    employer = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120, blank=True)
    start_month = models.CharField(max_length=20, blank=True)
    start_year = models.CharField(max_length=4, blank=True)
    end_month = models.CharField(max_length=20, blank=True)
    end_year = models.CharField(max_length=4, blank=True)
    description = models.TextField(blank=True)

class Skill(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_skills")
    name = models.CharField(max_length=200)
    level = models.CharField(max_length=30, blank=True)  # Beginner|Intermediate|Advanced|Expert
    award = models.CharField(max_length=200, blank=True)
    date_received = models.CharField(max_length=40, blank=True)
    presenter = models.CharField(max_length=200, blank=True)

class Interest(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="resume_interests")
    name = models.CharField(max_length=200)


# For the OTP-based password recovery (models)
import uuid, hashlib, random, string
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class PasswordReset(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code_hash  = models.CharField(max_length=128)     
    expires_at = models.DateTimeField()
    attempts   = models.PositiveIntegerField(default=0)
    verified   = models.BooleanField(default=False)
    reset_token= models.CharField(max_length=64, blank=True, null=True) 

    @staticmethod
    def new_code():
        return ''.join(random.choices(string.digits, k=6))

    @staticmethod
    def hash(s: str) -> str:
        return hashlib.sha256(s.encode()).hexdigest()

    @classmethod
    def create_for(cls, user):
        otp = cls.new_code()
        obj = cls.objects.create(
            user=user,
            code_hash=cls.hash(otp),
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        return obj, otp