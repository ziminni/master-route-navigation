from rest_framework import serializers
from .models import EventType, EventSchedule, Event, EventScheduleBlock, EventAttendance, EventApproval
from apps.Users.models import StudentProfile, FacultyProfile
from apps.Academics.models import Semester

class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = '__all__'

class EventScheduleBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventScheduleBlock
        fields = ['id', 'name', 'description']

class EventSerializer(serializers.ModelSerializer):
    event_type_name = serializers.CharField(source='event_type.event_type', read_only=True)
    schedule_block_name = serializers.CharField(source='event_schedule_block.name', read_only=True)
    semester_info = serializers.CharField(source='sem_id.name', read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'id', 'event_schedule_block', 'event_type', 'sem_id', 'title', 'venue', 
            'event_status', 'event_type_name', 'schedule_block_name', 'semester_info'
        ]
        read_only_fields = ('event_status',)  #control status via separate endpoints

class EventScheduleSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='user_id.get_full_name', read_only=True)
    event_title = serializers.CharField(source='event_id.title', read_only=True)
    schedule_block_name = serializers.CharField(source='event_schedule_block_id.name', read_only=True)
    
    class Meta:
        model = EventSchedule
        fields = '__all__'

class EventAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student_id.get_full_name', read_only=True)
    event_title = serializers.CharField(source='event_id.title', read_only=True)
    
    class Meta:
        model = EventAttendance
        fields = '__all__'

class EventApprovalSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver_id.get_full_name', read_only=True)
    event_title = serializers.CharField(source='event_id.title', read_only=True)
    
    class Meta:
        model = EventApproval
        fields = '__all__'

# Additional serializers for nested representations if needed
class EventDetailSerializer(EventSerializer):
    """Extended serializer for detailed event view with nested relationships"""
    schedules = EventScheduleSerializer(many=True, read_only=True, source='eventschedule_set')
    approvals = EventApprovalSerializer(many=True, read_only=True, source='eventapproval_set')
    attendance = EventAttendanceSerializer(many=True, read_only=True, source='eventattendance_set')
    
    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ['schedules', 'approvals', 'attendance']

class EventScheduleBlockDetailSerializer(EventScheduleBlockSerializer):
    """Extended serializer for schedule block with nested events"""
    events = EventSerializer(many=True, read_only=True, source='event_set')
    
    class Meta(EventScheduleBlockSerializer.Meta):
        fields = EventScheduleBlockSerializer.Meta.fields + ['events']

# Specialized serializers for specific operations
class EventStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer specifically for updating event status"""
    class Meta:
        model = Event
        fields = ['event_status']

class EventApprovalCreateSerializer(serializers.ModelSerializer):
    """Serializer specifically for creating event approvals with validation"""
    
    def validate(self, data):
        # Ensure an event can only be approved once
        event = data.get('event_id')
        if EventApproval.objects.filter(event_id=event).exists():
            raise serializers.ValidationError("This event has already been approved.")
        return data
    
    class Meta:
        model = EventApproval
        fields = '__all__'