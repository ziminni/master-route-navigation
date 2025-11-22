from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

# serializers.py
from rest_framework import serializers
from django.conf import settings

from .models import *
from ..Users.models import Program
from ..Users.serializers import ProgramSerializer


# MODULE 2

class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = "__all__"

    #TODO
    # add validate() method to validate start date and end date, and whether those dates coincide with the academic year


class SemesterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ["id", "is_active"]
        # read_only_fields = ["id"]

class CurriculumSerializer(serializers.ModelSerializer):
    # Uses the program id for write operations
    program_id = serializers.PrimaryKeyRelatedField(queryset=Program.objects.all(), write_only=True)
    # Returns full program details for read operations
    program_details = ProgramSerializer(source="program")

    class Meta:
        model = Curriculum
        fields = ["id", "program_id", "program_details", "revision_year", "is_active"]
        read_only_fields = ["program_details"]

class CurriculumUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = ["id", "revision_year", "is_active"]
        # read_only_fields = ["id"]

class SectionSerializer(serializers.ModelSerializer):
    """
    Used when retrieving or deleting a section.
    """
    curriculum_details = CurriculumSerializer(source="curriculum")
    semester_details = SemesterSerializer(source="semester")
    code = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "name", "code", "curriculum_details", "semester_details", "year", "type", "capacity"]
        read_only_fields = ["curriculum_details", "semester_details", "code"]

    def get_code(self, obj):
        return obj.code

class SectionListCreateSerializer(serializers.ModelSerializer):
    """
    Used when creating a new section or when retrieving all sections.
    """
    code = serializers.SerializerMethodField()

    class Meta:
        model = Section
        fields = ["id", "name", "code", "curriculum", "semester", "year", "type", "capacity"]
        read_only_fields = ["code"]

    def get_code(self, obj):
        return obj.code

class SectionUpdateSerializer(serializers.ModelSerializer):
    """
    Used when updating a section.
    """
    class Meta:
        model = Section
        fields = ["id", "name", "year", "type", "capacity"]
        # read_only_fields = ["id"]

class CourseSerializer(serializers.ModelSerializer):
    """
    Used when creating, retrieving or deleting a course.
    """
    curriculum_id = serializers.PrimaryKeyRelatedField(queryset=Curriculum.objects.all(), write_only=True)
    curriculum_details = CurriculumSerializer(source="curriculum")

    class Meta:
        model = Course
        fields = ["id", "code", "title", "units", "lec_hours", "lab_hours", "curriculum_id", "curriculum_details", "year_offered", "term_offered"]
        read_only_fields = ["curriculum_details"]

class CourseListSerializer(serializers.ModelSerializer):
    """
    Used when retrieving a list of courses.
    """
    class Meta:
        model = Course
        fields = "__all__"

class CourseUpdateSerializer(serializers.ModelSerializer):
    """
    Used when updating a course.
    """
    class Meta:
        model = Course
        fields = ["id", "code", "title", "units", "lec_hours", "lab_hours", "curriculum", "year_offered", "term_offered"]
        read_only_fields = ["curriculum"]

class CurriculumCourseSerializer(serializers.ModelSerializer):
    """
    Used when retrieving a list of all curriculums and their associated courses.
    """
    courses = CourseSerializer(many=True)
    program = serializers.StringRelatedField()

    class Meta:
        model = Curriculum
        fields = ["id", "program", "revision_year", "is_active", "courses"]
        read_only_fields = ["program", "revision_year", "is_active", "courses"]






#MODULE 3
class ScheduleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        # SELECT id, start_time, end_time, day_of_week FROM schedule_entry

        fields = ["id","start_time","end_time","day_of_week"]
        # Which fields should be returned by Django every time it is

#MODULE 3
class ScheduleEntrySerializer(serializers.ModelSerializer):
    day_of_week_display = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = ScheduleEntry
        fields = [
            'id',
            'schedule_block_id',
            'entry_name',
            'additional_context',
            'start_time',
            'end_time',
            'day_of_week',
            'day_of_week_display'
        ]
        read_only_fields = ['id']

#MODULE 3
class ScheduleBlockSerializer(serializers.ModelSerializer):
    # Includes nested schedule_entries with full entry details
    # Currently, it is better to refer more to this if viewing Schedules is the main intention
    # Not only the schedule entries, but the schedule blocks. This is particularlly useful for faculty/admin views
    # Nested serializer for schedule entries
    schedule_entries = ScheduleEntrySerializer(many=True, read_only=True)
    
    class Meta:
        model = ScheduleBlock
        fields = [
            'id',
            'user_id',
            'sem_id',
            'block_title',
            'schedule_entries'
        ]
        read_only_fields = ['id']

#MODULE 3
class ScheduleBlockCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleBlock
        fields = [
            'id',
            'user_id',
            'sem_id',
            'block_title'
        ]
        read_only_fields = ['id']

#MODULE 3
class ScheduleBlockUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleBlock
        fields = [
            'id',
            'block_title'
        ]
        read_only_fields = ['id', 'user_id', 'sem_id']

#MODULE 3
class ScheduleEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = [
            'id',
            'schedule_block_id',
            'entry_name',
            'additional_context',
            'start_time',
            'end_time',
            'day_of_week'
        ]
        read_only_fields = ['id']

#MODULE 3
class ScheduleEntryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleEntry
        fields = [
            'id',
            'entry_name',
            'additional_context',
            'start_time',
            'end_time',
            'day_of_week'
        ]
        read_only_fields = ['id', 'schedule_block_id']