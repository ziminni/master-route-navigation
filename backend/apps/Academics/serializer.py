from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

# serializers.py
from rest_framework import serializers
from django.conf import settings

from .models import ScheduleBlock, ScheduleEntry, Class, AcademicYear


# MODULE 2

class AcademicYearSerializer(serializers.ModelSerializer):
    class Meta:
        model = AcademicYear
        fields = '__all__'


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