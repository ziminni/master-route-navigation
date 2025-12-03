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
    Assessment, Score, Class, Enrollment
)
from ..Users.models import Program
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