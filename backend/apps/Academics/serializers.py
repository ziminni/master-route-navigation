from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed

# serializers.py
from rest_framework import serializers
from django.conf import settings

from .models import *
from .models import (
    GradingRubric, RubricComponent, Topic, Material, 
    Assessment, Score, Class, Enrollment, Attendance
)
from ..Users.models import Program, StudentProfile
from ..Users.serializers import ProgramSerializer
from ..Users.serializers import StudentProfileSerializer, BaseUserSerializer


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


class ClassSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving Class instances with full details.
    """
    course_details = CourseSerializer(source='course', read_only=True)
    section_details = SectionSerializer(source='section', read_only=True)
    semester_details = SemesterSerializer(source='semester', read_only=True)
    faculty_name = serializers.CharField(source='faculty.user.get_full_name', read_only=True)
    lecture_class_details = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = [
            'id', 'course', 'course_details', 'faculty', 'faculty_name',
            'section', 'section_details', 'semester', 'semester_details',
            'lecture_class', 'lecture_class_details'
        ]
        read_only_fields = ['id', 'course_details', 'section_details', 'semester_details', 'faculty_name']
    
    def get_lecture_class_details(self, obj):
        """Get basic details of the associated lecture class if this is a lab."""
        if obj.lecture_class:
            return {
                'id': obj.lecture_class.id,
                'course_code': obj.lecture_class.course.code,
                'course_title': obj.lecture_class.course.title
            }
        return None


class ClassCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Class instances.
    """
    class Meta:
        model = Class
        fields = ['id', 'course', 'faculty', 'section', 'semester', 'lecture_class']
        read_only_fields = ['id']
    
    def validate(self, data):
        """
        Validate that:
        1. The course belongs to the section's curriculum
        2. If lecture_class is provided, it exists and is for the same section/semester
        """
        course = data.get('course')
        section = data.get('section')
        semester = data.get('semester')
        lecture_class = data.get('lecture_class')
        
        # Validate course belongs to section's curriculum
        if course.curriculum != section.curriculum:
            raise serializers.ValidationError({
                'course': f'Course {course.code} does not belong to the curriculum of section {section.code}'
            })
        
        # Validate lecture_class if provided
        if lecture_class:
            if lecture_class.section != section:
                raise serializers.ValidationError({
                    'lecture_class': 'Lecture class must be for the same section'
                })
            if lecture_class.semester != semester:
                raise serializers.ValidationError({
                    'lecture_class': 'Lecture class must be for the same semester'
                })
        
        return data


class ClassUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Class instances.
    Only allows updating faculty and lecture_class.
    """
    class Meta:
        model = Class
        fields = ['id', 'faculty', 'lecture_class']
        read_only_fields = ['id']
    
    def validate_lecture_class(self, value):
        """Validate that lecture class is for the same section and semester."""
        if value:
            instance = self.instance
            if value.section != instance.section:
                raise serializers.ValidationError('Lecture class must be for the same section')
            if value.semester != instance.semester:
                raise serializers.ValidationError('Lecture class must be for the same semester')
        return value


class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving Enrollment instances with full details.
    """
    student_details = StudentProfileSerializer(source='student', read_only=True)
    class_details = ClassSerializer(source='enrolled_class', read_only=True)
    enrolled_by_name = serializers.CharField(source='enrolled_by.get_full_name', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = [
            'id', 'enrolled_class', 'class_details', 'student', 'student_details',
            'enrolled_at', 'enrolled_by', 'enrolled_by_name'
        ]
        read_only_fields = ['id', 'enrolled_at', 'class_details', 'student_details', 'enrolled_by_name']


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for enrolling a student in a class.
    """
    class Meta:
        model = Enrollment
        fields = ['id', 'enrolled_class', 'student', 'enrolled_by']
        read_only_fields = ['id', 'enrolled_by']
    
    def validate(self, data):
        """
        Validate that:
        1. The student is not already enrolled in the class
        2. The class has not exceeded capacity
        """
        enrolled_class = data.get('enrolled_class')
        student = data.get('student')
        
        # Check if student is already enrolled
        if Enrollment.objects.filter(enrolled_class=enrolled_class, student=student).exists():
            raise serializers.ValidationError({
                'student': f'Student is already enrolled in this class'
            })
        
        # Check class capacity
        current_enrollments = Enrollment.objects.filter(enrolled_class=enrolled_class).count()
        section_capacity = enrolled_class.section.capacity
        
        if current_enrollments >= section_capacity:
            raise serializers.ValidationError({
                'enrolled_class': f'Class has reached maximum capacity ({section_capacity})'
            })
        
        return data
    
    def create(self, validated_data):
        """Set enrolled_by to the current user making the request."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['enrolled_by'] = request.user
        return super().create(validated_data)


class BulkEnrollmentSerializer(serializers.Serializer):
    """
    Serializer for bulk enrolling multiple students in a class.
    """
    enrolled_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    students = serializers.PrimaryKeyRelatedField(
        queryset=StudentProfile.objects.all(),
        many=True
    )
    
    def validate(self, data):
        """
        Validate that:
        1. No duplicate students in the request
        2. None of the students are already enrolled
        3. Class has enough capacity
        """
        enrolled_class = data.get('enrolled_class')
        students = data.get('students')
        
        # Check for duplicates in request
        student_ids = [s.id for s in students]
        if len(student_ids) != len(set(student_ids)):
            raise serializers.ValidationError({
                'students': 'Duplicate students in enrollment list'
            })
        
        # Check if any student is already enrolled
        already_enrolled = Enrollment.objects.filter(
            enrolled_class=enrolled_class,
            student__in=students
        ).values_list('student__user__first_name', 'student__user__last_name')
        
        if already_enrolled:
            names = [f"{first} {last}" for first, last in already_enrolled]
            raise serializers.ValidationError({
                'students': f'The following students are already enrolled: {", ".join(names)}'
            })
        
        # Check capacity
        current_enrollments = Enrollment.objects.filter(enrolled_class=enrolled_class).count()
        section_capacity = enrolled_class.section.capacity
        new_total = current_enrollments + len(students)
        
        if new_total > section_capacity:
            raise serializers.ValidationError({
                'enrolled_class': f'Enrolling {len(students)} students would exceed capacity '
                                 f'({new_total}/{section_capacity})'
            })
        
        return data


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving Attendance records with full details.
    """
    student_details = StudentProfileSerializer(source='student', read_only=True)
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    class_details = ClassSerializer(source='class_instance', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Attendance
        fields = [
            'id', 'class_instance', 'class_details', 'student', 'student_details',
            'student_name', 'date', 'status', 'status_display', 'remarks',
            'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = [
            'id', 'updated_at', 'class_details', 'student_details',
            'student_name', 'updated_by_name', 'status_display'
        ]


class AttendanceCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating or updating attendance records.
    """
    class Meta:
        model = Attendance
        fields = ['id', 'class_instance', 'student', 'date', 'status', 'remarks', 'updated_by']
        read_only_fields = ['id', 'updated_by']
    
    def validate(self, data):
        """
        Validate that:
        1. The student is enrolled in the class
        2. The date is not in the future
        """
        from datetime import date as dt_date
        
        class_instance = data.get('class_instance')
        student = data.get('student')
        date = data.get('date')
        
        # Check if student is enrolled in the class
        if not Enrollment.objects.filter(enrolled_class=class_instance, student=student).exists():
            raise serializers.ValidationError({
                'student': 'Student is not enrolled in this class'
            })
        
        # Check date is not in the future
        if date and date > dt_date.today():
            raise serializers.ValidationError({
                'date': 'Attendance date cannot be in the future'
            })
        
        return data
    
    def create(self, validated_data):
        """Set updated_by to the current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Set updated_by to the current user."""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class BulkAttendanceSerializer(serializers.Serializer):
    """
    Serializer for bulk recording attendance for multiple students.
    """
    class_instance = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all())
    date = serializers.DateField()
    attendance_records = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField()
        )
    )
    
    def validate_attendance_records(self, value):
        """
        Validate attendance records format.
        Expected format: [{"student": 1, "status": "present", "remarks": "..."}, ...]
        """
        from ..Users.models import StudentProfile
        
        for record in value:
            # Check required fields
            if 'student' not in record or 'status' not in record:
                raise serializers.ValidationError(
                    'Each record must have "student" and "status" fields'
                )
            
            # Validate student ID
            try:
                student_id = int(record['student'])
                if not StudentProfile.objects.filter(id=student_id).exists():
                    raise serializers.ValidationError(f'Student with ID {student_id} does not exist')
            except (ValueError, TypeError):
                raise serializers.ValidationError(f'Invalid student ID: {record["student"]}')
            
            # Validate status
            valid_statuses = ['present', 'absent', 'late', 'excused']
            if record['status'] not in valid_statuses:
                raise serializers.ValidationError(
                    f'Invalid status "{record["status"]}". Must be one of: {", ".join(valid_statuses)}'
                )
        
        return value
    
    def validate(self, data):
        """Validate date and enrollment."""
        from datetime import date as dt_date
        
        date = data.get('date')
        class_instance = data.get('class_instance')
        attendance_records = data.get('attendance_records', [])
        
        # Check date is not in the future
        if date and date > dt_date.today():
            raise serializers.ValidationError({
                'date': 'Attendance date cannot be in the future'
            })
        
        # Check all students are enrolled
        student_ids = [int(record['student']) for record in attendance_records]
        enrolled_students = set(
            Enrollment.objects.filter(
                enrolled_class=class_instance,
                student_id__in=student_ids
            ).values_list('student_id', flat=True)
        )
        
        not_enrolled = set(student_ids) - enrolled_students
        if not_enrolled:
            raise serializers.ValidationError({
                'attendance_records': f'Students not enrolled in class: {list(not_enrolled)}'
            })
        
        return data


class RubricComponentSerializer(serializers.ModelSerializer):
    """
    Serializer for rubric components.
    Used for nested representation within GradingRubric.
    """
    class Meta:
        model = RubricComponent
        fields = ['id', 'name', 'percentage', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RubricComponentCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating individual rubric components.
    """
    class Meta:
        model = RubricComponent
        fields = ['id', 'rubric', 'name', 'percentage']
        read_only_fields = ['id']


class GradingRubricSerializer(serializers.ModelSerializer):
    """
    Full serializer for GradingRubric with nested components.
    Used for GET operations.
    """
    components = RubricComponentSerializer(many=True, read_only=True)
    academic_period_display = serializers.CharField(
        source='get_academic_period_display', 
        read_only=True
    )
    
    class Meta:
        model = GradingRubric
        fields = [
            'id', 'class_instance', 'academic_period', 
            'academic_period_display', 'term_percentage', 
            'components', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GradingRubricCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a GradingRubric with components.
    Accepts nested components in the request.
    """
    components = RubricComponentSerializer(many=True)
    
    class Meta:
        model = GradingRubric
        fields = [
            'id', 'class_instance', 'academic_period', 
            'term_percentage', 'components'
        ]
        read_only_fields = ['id']
    
    def validate_components(self, components):
        """Validate that components sum to 100%"""
        total = sum(comp['percentage'] for comp in components)
        if abs(total - 100) > 0.01:  # Allow for floating point errors
            raise serializers.ValidationError(
                f"Component percentages must sum to 100%. Current sum: {total}%"
            )
        return components
    
    def create(self, validated_data):
        """Create rubric with nested components"""
        components_data = validated_data.pop('components')
        rubric = GradingRubric.objects.create(**validated_data)
        
        for component_data in components_data:
            RubricComponent.objects.create(rubric=rubric, **component_data)
        
        return rubric


class GradingRubricUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating GradingRubric.
    Components are updated separately via their own endpoints.
    """
    class Meta:
        model = GradingRubric
        fields = ['id', 'term_percentage']
        read_only_fields = ['id', 'class_instance', 'academic_period']


class TopicSerializer(serializers.ModelSerializer):
    """
    Serializer for Topic model.
    """
    class Meta:
        model = Topic
        fields = [
            'id', 'class_instance', 'name', 'topic_number', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TopicCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating topics.
    """
    class Meta:
        model = Topic
        fields = ['id', 'class_instance', 'name', 'topic_number']
        read_only_fields = ['id']


class MaterialSerializer(serializers.ModelSerializer):
    """
    Full serializer for Material with related topic details.
    """
    topic_details = TopicSerializer(source='topic', read_only=True)
    created_by_details = BaseUserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = Material
        fields = [
            'id', 'class_instance', 'topic', 'topic_details',
            'title', 'description', 'is_published',
            'created_at', 'created_by', 'created_by_details', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'created_by', 'updated_at']


class MaterialListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing materials.
    """
    class Meta:
        model = Material
        fields = [
            'id', 'title', 'topic', 'is_published', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MaterialCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating materials.
    """
    class Meta:
        model = Material
        fields = [
            'id', 'class_instance', 'topic', 'title', 
            'description', 'is_published'
        ]
        read_only_fields = ['id']



class AssessmentSerializer(serializers.ModelSerializer):
    """
    Full serializer for Assessment with related details.
    """
    topic_details = TopicSerializer(source='topic', read_only=True)
    rubric_component_details = RubricComponentSerializer(
        source='rubric_component', read_only=True
    )
    created_by_details = BaseUserSerializer(source='created_by', read_only=True)
    academic_period_display = serializers.CharField(
        source='get_academic_period_display', read_only=True
    )
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'class_instance', 'rubric_component', 
            'rubric_component_details', 'topic', 'topic_details',
            'title', 'description', 'academic_period', 
            'academic_period_display', 'max_points', 'due_date', 
            'is_published', 'created_at', 'created_by', 
            'created_by_details', 'updated_at'
        ]
        read_only_fields = [
            'id', 'academic_period', 'created_at', 
            'created_by', 'updated_at'
        ]


class AssessmentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing assessments.
    """
    academic_period_display = serializers.CharField(
        source='get_academic_period_display', read_only=True
    )
    
    class Meta:
        model = Assessment
        fields = [
            'id', 'title', 'rubric_component', 'academic_period',
            'academic_period_display', 'max_points', 'due_date', 
            'is_published', 'created_at'
        ]
        read_only_fields = ['id', 'academic_period', 'created_at']


class AssessmentCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating assessments.
    academic_period is auto-set from rubric_component.
    """
    class Meta:
        model = Assessment
        fields = [
            'id', 'class_instance', 'rubric_component', 'topic',
            'title', 'description', 'max_points', 'due_date', 
            'is_published'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate that rubric_component belongs to the class"""
        rubric_component = data.get('rubric_component')
        class_instance = data.get('class_instance')
        
        if rubric_component and class_instance:
            if rubric_component.rubric.class_instance != class_instance:
                raise serializers.ValidationError(
                    "Rubric component does not belong to this class."
                )
        
        return data



class ScoreSerializer(serializers.ModelSerializer):
    """
    Full serializer for Score with related details.
    """
    student_details = StudentProfileSerializer(source='student', read_only=True)
    assessment_details = AssessmentListSerializer(source='assessment', read_only=True)
    uploaded_by_details = BaseUserSerializer(source='uploaded_by', read_only=True)
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Score
        fields = [
            'id', 'class_instance', 'student', 'student_details',
            'assessment', 'assessment_details', 'points', 
            'percentage', 'is_published', 'uploaded_at', 
            'uploaded_by', 'uploaded_by_details', 'updated_at'
        ]
        read_only_fields = [
            'id', 'uploaded_at', 'uploaded_by', 'updated_at'
        ]
    
    def get_percentage(self, obj):
        """Calculate percentage score"""
        return obj.percentage


class ScoreListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing scores.
    """
    percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Score
        fields = [
            'id', 'student', 'assessment', 'points', 
            'percentage', 'is_published', 'updated_at'
        ]
        read_only_fields = ['id', 'updated_at']
    
    def get_percentage(self, obj):
        return obj.percentage


class ScoreCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating scores.
    """
    class Meta:
        model = Score
        fields = [
            'id', 'class_instance', 'student', 'assessment', 
            'points', 'is_published'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate that points don't exceed assessment's max_points"""
        assessment = data.get('assessment')
        points = data.get('points')
        
        if assessment and points:
            if points > assessment.max_points:
                raise serializers.ValidationError(
                    f"Points ({points}) cannot exceed assessment's "
                    f"max points ({assessment.max_points})."
                )
            if points < 0:
                raise serializers.ValidationError(
                    "Points cannot be negative."
                )
        
        return data


class BulkScoreCreateSerializer(serializers.Serializer):
    """
    Serializer for bulk creating/updating scores for all students.
    Used when faculty sets same score for all students in a column.
    """
    assessment_id = serializers.IntegerField()
    points = serializers.IntegerField()
    is_published = serializers.BooleanField(default=False)
    
    def validate_points(self, value):
        """Validate points are non-negative"""
        if value < 0:
            raise serializers.ValidationError("Points cannot be negative.")
        return value
    
    def validate(self, data):
        """Validate assessment exists and points don't exceed max"""
        try:
            assessment = Assessment.objects.get(id=data['assessment_id'])
            if data['points'] > assessment.max_points:
                raise serializers.ValidationError(
                    f"Points ({data['points']}) cannot exceed assessment's "
                    f"max points ({assessment.max_points})."
                )
            data['assessment'] = assessment
        except Assessment.DoesNotExist:
            raise serializers.ValidationError("Assessment not found.")
        
        return data


class BulkScoreUploadSerializer(serializers.Serializer):
    """
    Serializer for bulk uploading (publishing) scores.
    Marks all scores for an assessment as published.
    """
    assessment_id = serializers.IntegerField()
    
    def validate_assessment_id(self, value):
        """Validate assessment exists"""
        if not Assessment.objects.filter(id=value).exists():
            raise serializers.ValidationError("Assessment not found.")
        return value


class StudentGradesSummarySerializer(serializers.Serializer):
    """
    Serializer for student's grade summary.
    Returns calculated grades for midterm, final term, and overall.
    """
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    class_id = serializers.IntegerField()
    class_name = serializers.CharField()
    
    midterm_grade = serializers.DecimalField(max_digits=5, decimal_places=2)
    final_term_grade = serializers.DecimalField(max_digits=5, decimal_places=2)
    final_grade = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    midterm_components = serializers.DictField()
    final_components = serializers.DictField()
    
    class Meta:
        fields = [
            'student_id', 'student_name', 'class_id', 'class_name',
            'midterm_grade', 'final_term_grade', 'final_grade',
            'midterm_components', 'final_components'
        ]



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