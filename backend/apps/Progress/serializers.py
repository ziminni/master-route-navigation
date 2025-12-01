from rest_framework import serializers
from .models import FacultyFeedbackMessage, FinalGrade

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
            # Term stored as Term.choices value (e.g. 'first'), convert if you want prettier labels.
            return f"{sem.academic_year} {sem.term}"
        except Exception:
            return ""