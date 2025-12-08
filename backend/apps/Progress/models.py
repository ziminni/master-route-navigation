# backend/apps/Progress/models.py
from django.db import models
from django.conf import settings

# These imports reference Module 2 tables
from apps.Academics.models import Course, Semester
from django.contrib.auth import get_user_model
User = get_user_model()

faculty_notes = models.TextField(blank=True, default="")

class FinalGrade(models.Model):
    """
    Final computed grade of a student for a course in a particular semester.
    """
    grade_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="final_grades"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="final_grades"
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="final_grades"
    )

    midterm_grade = models.CharField(max_length=4, null=True, blank=True)
    final_term_grade = models.CharField(max_length=4, null=True, blank=True)
    re_exam = models.CharField(max_length=4, null=True, blank=True)
    final_grade = models.CharField(max_length=4, null=True, blank=True)

    STATUS_CHOICES = [
        ("passed", "Passed"),
        ("failed", "Failed"),
        ("incomplete", "Incomplete"),
        ("withdrawn", "Withdrawn"),
    ]
    status = models.CharField(max_length=12, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.course.code} ({self.final_grade})"
    
    def is_passed(self):
        """Check if this grade represents a passed course"""
        return self.status.lower() == "passed"
    
    def get_category(self):
        """Determine the category of this course"""
        if not self.course:
            return "Unknown"
        
        course_code = self.course.code.upper() if self.course.code else ""
        course_title = self.course.title.upper() if self.course.title else ""
        
        if "GE" in course_code or "GENERAL" in course_title or "LIBERAL" in course_title:
            return "General Education"
        elif "CAPSTONE" in course_title or "THESIS" in course_title or "PROJECT" in course_title:
            return "Capstone"
        elif "INTERNSHIP" in course_title or "PRACTICUM" in course_title:
            return "Internship"
        elif "ELECT" in course_code or "ELECTIVE" in course_title:
            return "Elective"
        else:
            return "Core"  # For admin view, "Major" for student view


class GWA(models.Model):
    """
    General Weighted Average of a student for a particular semester.
    """
    gwa_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="gwa_records"
    )
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="gwa_records"
    )
    gwa = models.DecimalField(max_digits=5, decimal_places=4)

    class Meta:
        unique_together = ('student', 'semester')

    def __str__(self):
        return f"{self.student.get_full_name()} — {self.gwa} ({self.semester})"


class FacultyFeedbackMessage(models.Model):
    """
    Private academic notes from faculty to the student (part of Module 4).
    Read-only for Admin, read and delete for Student, send/write for Faculty.
    """
    id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feedback_received"
    )
    faculty = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feedback_given"
    )
    grade = models.ForeignKey(
        FinalGrade, 
        on_delete=models.CASCADE, 
        related_name="feedback_messages",
        null=True,
        blank=True
    )
    
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ("unread", "Unread"),
        ("read", "Read"),
    ]
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default="unread")

    def __str__(self):
        return f"Note to {self.student.username} from {self.faculty.username}"
    

class ClassScheduleInfo(models.Model):
    """
    Tracks schedule and room information for a class, with edit history.
    Faculty can edit schedule/room for their classes.
    """
    id = models.AutoField(primary_key=True)
    class_instance = models.OneToOneField(
        'Academics.Class', 
        on_delete=models.CASCADE, 
        related_name="schedule_info"
    )
    
    schedule = models.CharField(max_length=200, blank=True, default="")
    room = models.CharField(max_length=100, blank=True, default="")
    
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="schedule_updates"
    )
    
    def __str__(self):
        return f"{self.class_instance.course.code} - {self.schedule} ({self.room})"