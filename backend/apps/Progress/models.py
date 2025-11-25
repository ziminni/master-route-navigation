from django.db import models
from django.conf import settings

# These imports reference Module 2 tables
from apps.Academics.models import Course, Semester
from django.contrib.auth import get_user_model
User = get_user_model()



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
        FinalGrade, on_delete=models.CASCADE, related_name="feedback_messages"
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