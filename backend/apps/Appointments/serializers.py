from rest_framework import serializers
from .models import AvailabilityRule, Appointment

class AvailabilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRule
        fields = ["id", "faculty", "day_of_week", "start_time", "end_time", "semester", "slot_minutes"]

    def validate(self, data):
        if data['end_time'] <= data['start_time']:
            raise serializers.ValidationError("End time must be after start time.")
        
        return data

class AvailableSlotSerializer(serializers.Serializer):
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "faculty", "start_at", "end_at", "reason"]
        # Remove "student" and "status" - they should be set automatically
        # Remove "slots" - it doesn't exist in your model

    def validate(self, data):
        faculty = data["faculty"]
        start_at = data["start_at"]
        end_at = data["end_at"]

        # Basic validation
        if end_at <= start_at:
            raise serializers.ValidationError("End time must be after start time.")

        # Check for time conflicts with other appointments
        conflict = Appointment.objects.filter(
            faculty=faculty,
            start_at__lt=end_at,
            end_at__gt=start_at,
            status__in=[Appointment.PENDING, Appointment.APPROVED]
        ).exists()

        if conflict:
            raise serializers.ValidationError("Time slot conflicts with an existing appointment.")

        return data

class AppointmentListSerializer(serializers.ModelSerializer):
    faculty_name = serializers.CharField(
        source="faculty.user.get_full_name", read_only=True
    )
    student_name = serializers.CharField(
        source="student.user.get_full_name", read_only=True
    )

    class Meta:
        model = Appointment
        fields = [
            "id",
            "faculty",
            "faculty_name",
            "student",
            "student_name",
            "start_at",
            "end_at",
            "reason",
            "status",
            "created_at",
            "updated_at",
        ]

class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "status", "start_at", "end_at", "reason"]
        extra_kwargs = {
            'start_at': {'required': False},
            'end_at': {'required': False},
            'reason': {'required': False},
        }

    def validate(self, data):
        # Only validate time fields if they're being updated
        if 'start_at' in data or 'end_at' in data:
            start_at = data.get('start_at', self.instance.start_at)
            end_at = data.get('end_at', self.instance.end_at)
            
            if end_at <= start_at:
                raise serializers.ValidationError("End time must be after start time.")

        return data





