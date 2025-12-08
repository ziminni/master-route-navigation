# backend/apps/Progress/serializers.py
from rest_framework import serializers
from .models import FacultyFeedbackMessage, FinalGrade, ClassScheduleInfo


class FinalGradeSimpleSerializer(serializers.ModelSerializer):
    """
    Small serializer to expose course code and semester info for frontend grouping.
    """
    course_code = serializers.CharField(source="course.code", read_only=True)
    semester_academic_year = serializers.CharField(source="semester.academic_year", read_only=True)
    semester_term = serializers.CharField(source="semester.term", read_only=True)

    class Meta:
        model = FinalGrade
        fields = ("grade_id", "course_code", "semester_academic_year", "semester_term")


class FacultyFeedbackMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for FacultyFeedbackMessage. Accepts:
      - student (id)
      - faculty (id) will be set in view (faculty sending)
      - grade (grade_id)
      - message
    Returns additional read-only fields for convenience on frontend.
    """
    student_name = serializers.CharField(source="student.get_full_name", read_only=True)
    faculty_name = serializers.CharField(source="faculty.get_full_name", read_only=True)
    date_sent = serializers.DateTimeField(read_only=True)
    semester_label = serializers.SerializerMethodField()
    grade_simple = FinalGradeSimpleSerializer(source="grade", read_only=True)

    class Meta:
        model = FacultyFeedbackMessage
        fields = [
            "id",
            "student",
            "student_name",
            "faculty",
            "faculty_name",
            "grade",
            "grade_simple",
            "message",
            "date_sent",
            "status",
            "semester_label",
        ]
        read_only_fields = ["id", "faculty", "faculty_name", "date_sent", "student_name", "grade_simple", "semester_label"]

    def get_semester_label(self, obj):
        """
        Provide 'YYYY-YYYY term' style label using the linked FinalGrade -> semester.
        """
        try:
            sem = obj.grade.semester
            return f"{sem.academic_year} {sem.term}"
        except Exception:
            return ""


class ClassScheduleInfoSerializer(serializers.ModelSerializer):
    """Serializer for ClassScheduleInfo model"""
    class_name = serializers.CharField(source='class_instance.course.code', read_only=True)
    course_title = serializers.CharField(source='class_instance.course.title', read_only=True)
    section = serializers.CharField(source='class_instance.section.name', read_only=True)
    semester = serializers.SerializerMethodField()
    faculty_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    last_updated = serializers.DateTimeField(format="%b %d, %Y %I:%M %p", read_only=True)
    
    class Meta:
        model = ClassScheduleInfo
        fields = [
            'id', 'class_instance', 'class_name', 'course_title', 'section', 
            'semester', 'schedule', 'room', 'last_updated', 'updated_by', 
            'faculty_name'
        ]
        read_only_fields = [
            'id', 'class_instance', 'class_name', 'course_title', 'section', 
            'semester', 'last_updated', 'updated_by', 'faculty_name'
        ]
    
    def get_semester(self, obj):
        sem = obj.class_instance.semester
        return f"{sem.academic_year} - {sem.term}"


class ClassScheduleUpdateSerializer(serializers.Serializer):
    """Serializer for updating schedule and room"""
    schedule = serializers.CharField(max_length=200, required=True)
    room = serializers.CharField(max_length=100, required=True)
    
    def validate_schedule(self, value):
        if not value.strip():
            raise serializers.ValidationError("Schedule cannot be empty")
        return value.strip()
    
    def validate_room(self, value):
        if not value.strip():
            raise serializers.ValidationError("Room cannot be empty")
        return value.strip()