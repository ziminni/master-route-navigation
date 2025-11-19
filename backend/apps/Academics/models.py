from django.db import models

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
    """
    Represents an academic year with a start and end date.
    Only one academic year can be active at a time.
    """

    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "academics_academic_year"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["is_active"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["start_date", "end_date"], name="unique_ay_dates")
        ]


class Semester(models.Model):
    """
    Represents a semester within an academic year.
    Only one semester can be active at a time.
    """

    term = models.CharField(max_length=6, choices=Term.choices)
    start_date = models.DateField()
    end_date = models.DateField()
    academic_year = models.ForeignKey(AcademicYear, related_name="semesters", on_delete=models.PROTECT) # Academic year cannot be deleted if existing semesters are related to it
    is_active = models.BooleanField(unique=True)

    class Meta:
        db_table = "academics_semester"
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["academic_year"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["academic_year", "term"], name="unique_semester"),
            models.UniqueConstraint(fields=["start_date", "end_date"], name="unique_sem_dates")
        ]

class Curriculum(models.Model):
    """
    Defines a curriculum for a specific program and revision year.
    Only one curriculum per program can be active at a time.
    """

    program = models.ForeignKey("users.Program", related_name="curriculum", on_delete=models.CASCADE)
    revision_year = models.SmallIntegerField()
    is_active = models.BooleanField()

    class Meta:
        db_table = "academics_curriculum"
        ordering = ["-revision_year"]
        constraints = [
            models.UniqueConstraint(fields=["program", "is_active"], name="one_active_curriculum_per_program"),
        ]

class Section(models.Model):
    """
    Represents a section within a curriculum, semester, and year level.
    """

    name = models.CharField(max_length=7)
    curriculum = models.ForeignKey(Curriculum, related_name="sections", on_delete=models.PROTECT)
    semester = models.ForeignKey(Semester, related_name="sections", on_delete=models.PROTECT)
    year = models.CharField(max_length=1, choices=YearLevel.choices)
    type = models.CharField(max_length=3, choices=ClassType.choices)
    capacity = models.PositiveSmallIntegerField()

    class Meta:
        db_table = "academics_section"
        ordering = ["-semester", "name"]
        indexes = [
            models.Index(fields=["name", "semester"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["name", "semester", "type"], name="unique_section"),
        ]

class Track(models.Model):
    """
    Represents a specialization or track within a curriculum.
    """

    name = models.CharField(max_length=100)
    curriculum = models.ForeignKey(Curriculum, related_name="tracks", on_delete=models.CASCADE)

    class Meta:
        db_table = "academics_track"

class Course(models.Model):
    """
    Represents a course offered in a curriculum, including details like code, title, and units.
    """

    code = models.CharField(max_length=10, primary_key=True)
    title = models.CharField(max_length=100)
    units = models.PositiveSmallIntegerField()
    lec_hours = models.PositiveSmallIntegerField()
    lab_hours = models.PositiveSmallIntegerField()

    curriculum = models.ForeignKey(Curriculum, related_name="courses", on_delete=models.PROTECT)
    year_offered = models.CharField(max_length=1, choices=YearLevel.choices)
    term_offered = models.CharField(max_length=6, choices=Term.choices)
    track = models.ForeignKey(Track, related_name="courses", on_delete=models.PROTECT, null=True)
    # category

    class Meta:
        db_table = "academics_course"
        ordering = ["-curriculum", "code"]
        indexes = [
            models.Index(fields=["year_offered", "term_offered"]),
        ]

    # NOTES:
    # This design assumes course codes are not repeated for different program curricula
    # It also assumes that course title can be repeated for different courses, they only differ by course code

# Module 4 should handle this
class Prerequisite(models.Model):
    pass

class Class(models.Model):
    """
    Represents a class instance for a course, section, and semester, assigned to a faculty.
    """

    course = models.ForeignKey(Course, related_name="classes",on_delete=models.PROTECT)
    faculty = models.ForeignKey("users.FacultyProfile", related_name="assigned_classes",on_delete=models.SET_NULL, null=True)
    section = models.ForeignKey(Section, related_name="classes",on_delete=models.PROTECT)
    semester = models.ForeignKey(Semester, related_name="classes",on_delete=models.PROTECT)
    # schedule_block

    # Intermediary field between classes and students, so it's easier to query all the students enrolled in a specific class instead of aggregating enrolled students from the Enrollment table
    # IMPORTANT: it is not stored in the database
    # Can just use class_instance.students.all() to get all students enrolled in the class instance
    # AND student_instance.enrolled_classes.all() to retrieve all classes the student instance is enrolled in
    students = models.ManyToManyField("users.StudentProfile", through="Enrollment", related_name="enrolled_classes")

    class Meta:
        db_table = "academics_class"
        ordering = ["-semester", "course"]
        indexes = [
            models.Index(fields=["faculty", "semester"]),
        ]
        constraints = [
            # A section can only have one class instance for a specific course for a semester
            models.UniqueConstraint(fields=["course", "section", "semester"], name="unique_course_section_per_class_per_sem"),
        ]

class Enrollment(models.Model):
    """
    Links students to classes they are enrolled in.
    """

    enrolled_class = models.ForeignKey(Class, related_name="enrollments",on_delete=models.PROTECT)
    student = models.ForeignKey("users.StudentProfile", related_name="class_enrollments",on_delete=models.PROTECT) # PROTECT for now
    enrolled_at = models.DateTimeField(auto_now_add=True)
    enrolled_by = models.ForeignKey("users.BaseUser", related_name="enrolling_officer",on_delete=models.SET_NULL, null=True) # debatable

    class Meta:
        db_table = "academics_enrollments"
        ordering = ["-enrolled_at", "enrolled_class"]
        indexes = [
            models.Index(fields=["enrolled_class", "student"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["enrolled_class", "student"], name="one_enrollment_per_class_per_student"),
        ]

class GradingRubric(models.Model):
    class_instance = models.ForeignKey(Class, related_name="grading_rubrics",on_delete=models.CASCADE)
    academic_period = models.CharField(max_length=7, choices=AcademicPeriod.choices)

    class Meta:
        db_table = "academics_grading_rubric"

class RubricComponent(models.Model):
    rubric = models.ForeignKey(GradingRubric, related_name="components",on_delete=models.PROTECT) # debatable
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
    class_instance = models.ForeignKey(Class, related_name="topics",on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "academics_topic"

class Material(models.Model):
    class_instance = models.ForeignKey(Class, related_name="materials",on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name="materials",on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("users.BaseUser", related_name="uploaded_materials",on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academics_material"

class Assessment(models.Model):
    class_instance = models.ForeignKey(Class, related_name="assessments",on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, related_name="assessments",on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    rubric_component = models.ForeignKey(RubricComponent, related_name="assessments",on_delete=models.PROTECT)
    max_points = models.IntegerField()
    due_date = models.DateTimeField()
    is_published = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("users.BaseUser", related_name="uploaded_assessments",on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academics_assessment"

class Score(models.Model):
    class_instance = models.ForeignKey(Class, related_name="student_scores",on_delete=models.CASCADE)
    student = models.ForeignKey("users.StudentProfile", related_name="scores",on_delete=models.PROTECT) # protect for now
    assessment = models.ForeignKey(Assessment, related_name="student_scores",on_delete=models.PROTECT)
    points = models.PositiveIntegerField()
    is_published = models.BooleanField(default=False)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey("users.BaseUser", related_name="uploaded_scores",on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "academics_score"
        constraints = [
            models.UniqueConstraint(fields=['student', 'assessment'], name='unique_student'),
        ]

class Attendance(models.Model):
    """
    Records a student's attendance status for a class session.
    """

    class_instance = models.ForeignKey(Class, related_name="attendance",on_delete=models.CASCADE)
    student = models.ForeignKey("users.StudentProfile", related_name="attendance",on_delete=models.PROTECT)
    date = models.DateField()

    class Status(models.TextChoices):
        PRESENT = "present", "Present"
        ABSENT = "absent", "Absent"
        LATE = "late", "Late"
        EXCUSED = "excused", "Excused"

    status = models.CharField(max_length=7, choices=Status.choices)
    remarks = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("users.BaseUser", related_name="recorded_attendance",on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "academics_attendance"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date", "class_instance"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=['class_instance','student','date'], name="one_attendance_per_student_per_session"),
        ]



#MODULE 3
class ScheduleBlock(models.Model):
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