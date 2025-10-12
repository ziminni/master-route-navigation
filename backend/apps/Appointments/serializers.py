from rest_framework import serializers
from .models import AppointmentScheduleBlock, AppointmentSchreduleEntry, Appointment

class AppointmentScheduleBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentScheduleBlock
        fields = ["id", "faculty"]

class AppointmentSchreduleEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = AppointmentSchreduleEntry
        fields = ["id", "start_time", "end_time", "day_of_week"]

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["id", "student", "appointment_schedule_entry", "additional_details", "address", "status", "appointment_date", "created_at", "updated_at", "image_path"]