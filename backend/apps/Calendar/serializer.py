from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import CalendarEntry, CalendarLogs, Holiday

# Serializer for ContentType (for source_ct field)
class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ['id', 'app_label', 'model']

# CalendarEntry serializer
class CalendarEntrySerializer(serializers.ModelSerializer):
    source_ct = ContentTypeSerializer(read_only=True)
    source_ct_id = serializers.PrimaryKeyRelatedField(
        queryset=ContentType.objects.all(),
        source='source_ct',
        write_only=True
    )
    source_id = serializers.IntegerField()
    title = serializers.CharField()
    start_at = serializers.DateTimeField()
    end_at = serializers.DateTimeField()
    location = serializers.CharField(required=False, allow_blank=True)
    all_day = serializers.BooleanField(default=False)
    is_public = serializers.BooleanField(default=True)
    tags = serializers.JSONField()
    org_status = serializers.CharField(required=False, allow_blank=True)
    org_id = serializers.IntegerField(required=False)
    section_id = serializers.IntegerField(required=False)
    semester_id = serializers.IntegerField(required=False)

    class Meta:
        model = CalendarEntry
        fields = [
            'id', 'source_ct', 'source_ct_id', 'source_id', 'title', 'start_at', 'end_at',
            'all_day', 'location', 'is_public', 'tags', 'org_status', 'org_id', 'section_id', 'semester_id'
        ]

# CalendarLogs serializer
class CalendarLogsSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.get_full_name', read_only=True)

    class Meta:
        model = CalendarLogs
        fields = [
            'id', 'event', 'event_title', 'action', 'performed_by', 'performed_by_name', 'timestamp', 'details'
        ]

# Holiday serializer
class HolidaySerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Holiday
        fields = [
            'id', 'name', 'date', 'description', 'created_by', 'created_by_name', 'created_at'
        ]

