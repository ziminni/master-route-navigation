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

class SemesterUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ["id", "is_active"]
        read_only_fields = ["id"]

class CurriculumSerializer(serializers.ModelSerializer):
    # Uses the program id for write operations
    program_id = serializers.PrimaryKeyRelatedField(queryset=Program.objects.all(), write_only=True)
    # Returns full program details for read operations
    program_details = ProgramSerializer(source="program_id", read_only=True)

    class Meta:
        model = Curriculum
        fields = ["id", "program_id", "program_details", "revision_year", "is_active"]

class CurriculumUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curriculum
        fields = ["id", "revision_year", "is_active"]
        read_only_fields = ["id"]

class SectionSerializer(serializers.ModelSerializer):
    curriculum_id = serializers.PrimaryKeyRelatedField(queryset=Curriculum.objects.all(), write_only=True)
    curriculum_details = CurriculumSerializer(source="curriculum_id", read_only=True)
    semester_details = SemesterSerializer(source="semester_id", read_only=True)
    semester_id = serializers.PrimaryKeyRelatedField(queryset=Semester.objects.all(), write_only=True)

    class Meta:
        model = Section
        fields = ["id", "name", "curriculum_id", "curriculum_details", "semester_id", "semester_details", "year", "type", "capacity"]




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