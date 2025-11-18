from rest_framework import serializers
from Organizations.models import EventType, EventSchedule, Event, EventScheduleBlock, EventAttendance, EventApproval
from Users.models import StudentProfile, FacultyProfile
from Academics.models import Semester

class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = '__all__'

class EventScheduleBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventScheduleBlock
        fields = '__all__'

class EventScheduleSerializer(serializers.ModelSerializer):
    user_id_details = serializers.PrimaryKeyRelatedField(read_only=True)
    event_id_details = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = EventSchedule
        fields = '__all__'
        read_only_fields = ('creation_date',)

class EventSerializer(serializers.ModelSerializer):
    event_type_details = EventTypeSerializer(source='event_type', read_only=True)
    event_schedule_details = EventScheduleSerializer(source='event_schedule', read_only=True)
    event_schedule_block_details = EventScheduleBlockSerializer(source='event_schedule_block', read_only=True)
    sem_id_details = serializers.PrimaryKeyRelatedField(source='sem_id', read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'

class EventAttendanceSerializer(serializers.ModelSerializer):
    event_id_details = EventSerializer(source='event_id', read_only=True)
    student_id_details = serializers.PrimaryKeyRelatedField(source='student_id', read_only=True)
    
    class Meta:
        model = EventAttendance
        fields = '__all__'

class EventApprovalSerializer(serializers.ModelSerializer):
    event_id_details = EventSerializer(source='event_id', read_only=True)
    approver_id_details = serializers.PrimaryKeyRelatedField(source='approver_id', read_only=True)
    
    class Meta:
        model = EventApproval
        fields = '__all__'
        read_only_fields = ('approved_at',)