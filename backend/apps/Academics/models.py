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
        db_table = "academic_year"

class Semester(models.Model):
    term = models.CharField(max_length=6, choices=Term.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.PROTECT) # Academic year cannot be deleted if existing semesters are related to it
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "semester"

class Curriculum(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE)
    revision_year = models.CharField(max_length=4)
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "curriculum"

class Section(models.Model):
    name = models.CharField(max_length=6)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.PROTECT)
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT)
    year = models.CharField(max_length=1, choices=YearLevel.choices)
    type = models.CharField(max_length=3, choices=ClassType.choices)
    capacity = models.IntegerField()

    class Meta:
        db_table = "section"

class Track(models.Model):
    name = models.CharField(max_length=100)
    curriculum = models.ForeignKey(Curriculum, on_delete=models.CASCADE)

    class Meta:
        db_table = "track"

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
        db_table = "course"

class Prerequisite(models.Model):
    pass

class Class(models.Model):
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    faculty = models.ForeignKey(FacultyProfile, on_delete=models.SET_NULL, null=True)
    section = models.ForeignKey(Section, on_delete=models.PROTECT)
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT)
    # schedule_block

    class Meta:
        db_table = "class"

class Enrollees(models.Model):
    enrolled_class = models.ForeignKey(Class, on_delete=models.PROTECT)
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT) # PROTECT for now
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True) # debatable

    class Meta:
        db_table = "enrollees"

class GradingRubric(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    academic_period = models.CharField(max_length=7, choices=AcademicPeriod.choices)

    class Meta:
        db_table = "grading_rubric"

class RubricComponent(models.Model):
    rubric = models.ForeignKey(GradingRubric, on_delete=models.PROTECT) # debatable
    name = models.CharField(max_length=20)
    percentage = models.DecimalField(decimal_places=2, max_digits=4)

    class Meta:
        db_table = "rubric_component"

class Topic(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "topic"

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
        db_table = "material"

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
        db_table = "assessment"# A bit of an err here got fixed

class Score(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.PROTECT) # protect for now
    assessment = models.ForeignKey(Assessment, on_delete=models.PROTECT)
    points = models.IntegerField()
    is_published = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "score"

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
        db_table = "attendance"





#MODULE 3
class ScheduleBlock(models.Model):
    user_id = models.ForeignKey(StudentProfile, on_delete=models.CASCADE) #Checks the student who owns this block
    #TODO
    # Semester is not working out for now, Semester ain't available
    # btw, in the database diagram it says "semesters", I rewrote it into "Semester"
    # since that's how the tables will be named in the end
    sem_id = models.ForeignKey('Semester', on_delete= models.PROTECT)
    block_title = models.CharField(max_length=50)   # VARCHAR(50)

    class Meta:
        db_table = "schedule_block"

#MODULE 3
class ScheduleEntry(models.Model):
    # id already assumed here
    schedule_block_id = models.ForeignKey(ScheduleBlock, on_delete=models.CASCADE)#This way,
    #if the block is deleted, all entries under it are also deleted
    entry_name = models.CharField(max_length=20)
    additional_context = models.CharField(max_length=50)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    # ENUM
    class DayOfWeek(models.TextChoices):
        SUN = "sun", "Sunday"
        MON = "mon", "Monday"
        TUE = "tue", "Tuesday"
        WED = "wed", "Wednesday"
        THU = "thu", "Thursday"
        FRI = "fri", "Friday"
        SAT = "sat", "Saturday"

    day_of_week = models.CharField(
        max_length=3,
        choices=DayOfWeek.choices,
        default=DayOfWeek.TUE
    )
    class Meta:
        db_table = "schedule_entry"