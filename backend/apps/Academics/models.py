from django.db import models
from apps.Users.models import Program, FacultyProfile, StudentProfile, BaseUser as User

# Enums

class Term(models.TextChoices):
    first = "first", "First Semester"
    second = "second", "Second Semester"
    summer = "summer", "Summer"

class YearLevel(models.TextChoices):
    first = "1", "First Year"
    second = "2", "Second Year"
    third = "3", "Third Year"
    fourth = "4", "Fourth Year"

class AcademicPeriod(models.TextChoices):
    midterm = "midterm", "Midterm"
    finals = "finals", "Final Term"

class ClassType(models.TextChoices):
    lec = "lec", "Lecture"
    lab = "lab", "Laboratory"


# Models

class AcademicYear(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "academics_academic_year"

class Semester(models.Model):
    term = models.CharField(max_length=6, choices=Term.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT) # Academic year cannot be deleted if existing semesters are related to it
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "academics_semester"

class Curriculum(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    revision_year = models.CharField(max_length=4)
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "academics_curriculum"

class Section(models.Model):
    name = models.CharField(max_length=6)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.PROTECT)
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT)
    year = models.CharField(max_length=1, choices=YearLevel.choices)
    type = models.CharField(max_length=3, choices=ClassType.choices)
    capacity = models.IntegerField()

    class Meta:
        db_table = "academics_section"

class Track(models.Model):
    name = models.CharField(max_length=100)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)

    class Meta:
        db_table = "academics_track"

class Course(models.Model):
    title = models.CharField(max_length=100)
    units = models.IntegerField()
    lec_hours = models.IntegerField()
    lab_hours = models.IntegerField()

    curriculum = models.ForeignKey(Curriculum, on_delete=models.PROTECT)
    year_offered = models.CharField(max_length=1, choices=YearLevel.choices)
    term_offered = models.CharField(max_length=6, choices=Term.choices)
    track = models.ForeignKey(Track, on_delete=models.PROTECT, null=True)
    # category

    class Meta:
        db_table = "academics_course"

class Prerequisite(models.Model):
    pass

class Class(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.SET_NULL, null=True)
    section = models.ForeignKey(Section, on_delete=models.PROTECT)
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT)
    # schedule_block

    class Meta:
        db_table = "academics_class"

class Enrollees(models.Model):
    enrolled_class = models.ForeignKey(Class, on_delete=models.PROTECT)
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT) # PROTECT for now
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # debatable

    class Meta:
        db_table = "academics_enrollees"
        constraints = [

        ]

class GradingRubric(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    academic_period = models.CharField(max_length=7, choices=AcademicPeriod.choices)

    class Meta:
        db_table = "academics_grading_rubric"

class RubricComponent(models.Model):
    rubric = models.ForeignKey(GradingRubric, on_delete=models.PROTECT) # debatable
    name = models.CharField(max_length=20)
    percentage = models.DecimalField(decimal_places=2, max_digits=4)

    class Meta:
        db_table = "academics_rubric_component"
        constraints = [
            models.UniqueConstraint(
                fields=['rubric','name'],
                name="unique_rubric_component",
            )
        ]

class Topic(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "academics_topic"

class Material(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    topic_id = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academics_material"

class Assessment(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    topic_id = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    rubric_component = models.ForeignKey(RubricComponent, on_delete=models.PROTECT)
    max_points = models.IntegerField()
    due_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academics_assessment"

class Score(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT) # protect for now
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT)
    points = models.PositiveIntegerField()
    is_published = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academics_score"
        constraints = [
            models.UniqueConstraint(fields=['student', 'assessment'], name='unique_student'),
        ]

class Attendance(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT)
    date = models.DateField()

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    status = models.CharField(max_length=7, choices=Status.choices)
    remarks = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "academics_attendance"
        constraints = [
            models.UniqueConstraint(
                fields=['class_id','student','date'],
                name="one_attendance_per_student_per_session"
            )
        ]



