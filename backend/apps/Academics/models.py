from django.db import models
from backend.apps.Users import models as user_model
from backend.apps.Admin import models as admin_model

# Create your models here.

class Prerequisite(models.Model):
    course_id = models.IntegerField()
    prerequisite_course = models.IntegerField()

    class Meta:
        db_table = "prerequisites"
        indexes = [
            models.Index(fields=['course_id, prerequisite_course'], name="idx_prereq_course")
            # Find all courses that has this prerequisite
        ]

class Curriculum(models.Model):
    # id already assumed to be here

    program_id = models.ForeignKey(user_model.Program, on_delete=models.PROTECT)
    # Foreign keys
    # Cascade on delete -> If we delete a program entry from Program tables, then the value here will also be deleted
    # Restrict on delete -> If there is a child entry on another table, the value from the Programs table will not be deleted

    # Boolean column
    is_active = models.BooleanField()

    class Meta:
        db_table = "curriculum"


class Course(models.Model):
    title = models.CharField(max_length=70)     # VARCHAR(70)
    units = models.SmallIntegerField()          # SMALLINT
    curriculum_id = models.ForeignKey(Curriculum, on_delete=models.PROTECT)

    # Create a Meta class here....
    class Meta:
        db_table = "courses"
        # Find all courses with the curriculum ID
#MODULE 3
class ScheduleBlock(models.Model):
    user_id = models.ForeignKey(user_model.BaseUser, on_delete=models.PROTECT)
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
    schedule_block_id = models.ForeignKey(ScheduleBlock)
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

class FinalGrade(models.Model):
    # id

    # Sample Enum
    class Statuses(models.TextChoices):
        PASSED = "pss", "Passed"
        FAILED = "fld", "Failed"
        INC = "inc", "Incomplete"

    status = models.CharField(
        max_length=3,
        choices=Statuses.choices
    )


class Class(models.Model):
    faculty_id = models.ForeignKey(user_model.FacultyProfile, on_delete=models.PROTECT, null=True)
    course_id  = models.ForeignKey(Course, on_delete=models.PROTECT, null=False)
    section_id = models.IntegerField()          # Change to ForeignKey
    schedule_block_id = models.ForeignKey("ScheduleBlock", on_delete=models.PROTECT)
    # Change to models.ForeignKey when schedule block is created:Done
    semester_id = models.IntegerField()         # Foreign Key

    is_archived = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)    # Auto_now_add is only executed for Create Operations
    updated_at = models.DateTimeField(auto_now=True)        # Auto_now is every time the entry is modified

    # SELECT * FROM classes ORDER BY created_at, is_archived, semester_id

    class Meta:
        db_table  = "classes"
        ordering  = ["-created_at","-is_archived","-semester_id"]
        indexes   = [
            # SELECT * FROM classes WHERE semester_id = 1 AND course_id = 47

            models.Index(fields=["semester_id", "course_id"]),
            # Find classes at this semester with a particular course ID
            # Find classes at 1st semester with the ITCC47 course

            models.Index(fields=["course_id", "section_id"]),
            # Find all sections with this course ID
            # Find classes where the section has the PE34 course
            # Each section should have unique combination of section_id and course_id

            # class_id = 1, section_id = 1, course_id = 34  -> This is the original entry
            # class_id = 1, section_id = 1, course_id = 34  -> This is not okay, no duplication
            # class_id = 1, section_id = 2, course_id = 34  -> This is okay

            models.Index(fields=["is_archived"]),
        ]

    def __str__(self):
        return f"{self.course_id} / sec {self.section_id} / sem {self.semester_id}"