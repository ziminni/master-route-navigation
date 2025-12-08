from django.shortcuts import render

# views.py
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import ScheduleBlock, ScheduleEntry, Semester
from .serializers import *
from django.shortcuts import get_object_or_404

from django.db.models import Prefetch, Q
from decimal import Decimal

from .models import (
    GradingRubric, RubricComponent, Topic, Material,
    Assessment, Score, Class, Enrollment, Attendance
)
from .serializers import (
    GradingRubricSerializer, GradingRubricCreateSerializer,
    GradingRubricUpdateSerializer, RubricComponentSerializer,
    RubricComponentCreateUpdateSerializer, TopicSerializer,
    TopicCreateUpdateSerializer, MaterialSerializer,
    MaterialListSerializer, MaterialCreateUpdateSerializer,
    AssessmentSerializer, AssessmentListSerializer,
    AssessmentCreateUpdateSerializer, ScoreSerializer,
    ScoreListSerializer, ScoreCreateUpdateSerializer,
    BulkScoreCreateSerializer, BulkScoreUploadSerializer,
    StudentGradesSummarySerializer,
    ClassSerializer, ClassCreateSerializer, ClassUpdateSerializer,
    EnrollmentSerializer, EnrollmentCreateSerializer, BulkEnrollmentSerializer,
    AttendanceSerializer, AttendanceCreateUpdateSerializer, BulkAttendanceSerializer
)


class BaseCRUDViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for CRUD endpoints which require admin privileges for write operations, but allow access to all authenticated users for write operations.

    GET: Accessible to all authenticated users.
    POST, PUT, PATCH, DELETE: Accessible only to users with admin privileges.
    """

    def get_permissions(self):
        """
        General method that restricts write operations to admin users while only allowing write operations to authenticated users.
        """
        if self.request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]


#TODO
# validate semester dates
class SemesterViewSet(BaseCRUDViewSet):
    """
    API endpoint for Semesters.

    For /api/academics/semesters/
    GET:
        Retrieves a list of semesters.

    POST:
        Create a new semester.
        Required fields:
            - term (str)
            - start_date (str)
            - end_date (str)
            - academic_year (str)
            - is_active (bool)

    For /api/academics/semesters/{semester_id}/
    GET:
        Retrieves a single semester.

    PUT or PATCH:
        Update an existing semester.
        Required fields:
            - is_active (bool)

    DELETE:
        Delete an existing semester.
    """
    queryset = Semester.objects.all()

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return SemesterUpdateSerializer
        return SemesterSerializer

class ActiveSemesterRetrieveAPIView(generics.RetrieveAPIView):
    """
    API endpoint for retrieving the active semester.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = SemesterSerializer

    def get_object(self):
        return get_object_or_404(Semester, is_active=True)

class CurriculumViewSet(BaseCRUDViewSet):
    """
    API endpoint for Curriculums.

    For /api/academics/curriculums/
    GET:
        Retrieves a list of curriculums.

    POST:
        Create a new curriculum.
        Required fields:
            - program_id (int)
            - revision_year (str)
            - is_active (bool)

    For /api/academics/curriculums/{curriculum_id}/
    GET:
        Retrieves a single curriculum.

    PUT or PATCH:
        Update an existing curriculum.
        Required fields:
        - revision_year (str)
        - is_active (bool)

    DELETE:
        Delete an existing curriculum.
    """
    queryset = Curriculum.objects.all()

    def get_serializer_class(self):
        if self.action in ["update", "partial_update"]:
            return CurriculumUpdateSerializer
        return CurriculumSerializer

class SectionViewSet(BaseCRUDViewSet):
    """
    API endpoint for Sections.

    For /api/academics/sections/
    GET:
        Returns a list of sections.

    POST:
        Creates a new section.
        Required fields:
            - name (str)
            - curriculum_id (int)
            - semester_id (int)
            - year (str)
            - type (str)
            - capacity (int)

    For /api/academics/sections/{section_id}/
    GET:
        Returns a single section with complete object details for curriculum and semester fields.

    PUT or PATCH:
        Updates an individual section.
        Required fields:
            - name (str)
            - year (str)
            - type (str)
            - capacity (int)

    DELETE:
        Deletes an individual section.
    """
    queryset = Section.objects.all()

    def get_serializer_class(self):
        if self.action in ["list", "create"]:
            return SectionListCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return SectionUpdateSerializer
        return SectionSerializer

class CourseViewSet(BaseCRUDViewSet):
    queryset = Course.objects.all()

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        elif self.action in ["update", "partial_update"]:
            return CourseUpdateSerializer
        return CourseSerializer


class ClassViewSet(BaseCRUDViewSet):
    """
    API endpoint for managing Class instances.
    
    GET: List all classes or retrieve a specific class
    POST: Create a new class (admin only)
    PUT/PATCH: Update a class (admin only)
    DELETE: Delete a class (admin only)
    """
    queryset = Class.objects.select_related(
        'course', 'faculty', 'section', 'semester', 'lecture_class'
    ).all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return ClassCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ClassUpdateSerializer
        return ClassSerializer
    
    def get_queryset(self):
        """
        Optionally filter classes by semester, section, course, or faculty.
        """
        queryset = super().get_queryset()
        
        # Filter by semester
        semester_id = self.request.query_params.get('semester')
        if semester_id:
            queryset = queryset.filter(semester_id=semester_id)
        
        # Filter by section
        section_id = self.request.query_params.get('section')
        if section_id:
            queryset = queryset.filter(section_id=section_id)
        
        # Filter by course
        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        # Filter by faculty
        faculty_id = self.request.query_params.get('faculty')
        if faculty_id:
            queryset = queryset.filter(faculty_id=faculty_id)
        
        return queryset


class EnrollmentListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating enrollments.
    
    GET: List all enrollments for a specific class
    POST: Enroll a student in a class (admin only)
    """
    serializer_class = EnrollmentSerializer
    
    def get_permissions(self):
        """Admin only for POST, authenticated for GET."""
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Get enrollments for a specific class."""
        class_id = self.kwargs.get('class_id')
        return Enrollment.objects.filter(enrolled_class_id=class_id).select_related(
            'student', 'enrolled_class', 'enrolled_by'
        )
    
    def get_serializer_class(self):
        """Use create serializer for POST."""
        if self.request.method == 'POST':
            return EnrollmentCreateSerializer
        return EnrollmentSerializer
    
    def perform_create(self, serializer):
        """Set the enrolled_by to the current user."""
        serializer.save(enrolled_by=self.request.user)


class EnrollmentDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    API endpoint for retrieving or deleting a specific enrollment.
    
    GET: Retrieve enrollment details
    DELETE: Unenroll a student (admin only)
    """
    queryset = Enrollment.objects.select_related('student', 'enrolled_class', 'enrolled_by')
    serializer_class = EnrollmentSerializer
    
    def get_permissions(self):
        """Admin only for DELETE, authenticated for GET."""
        if self.request.method == 'DELETE':
            return [IsAdminUser()]
        return [IsAuthenticated()]


class BulkEnrollmentAPIView(APIView):
    """
    API endpoint for bulk enrolling multiple students in a class.
    
    POST: Enroll multiple students at once (admin only)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, class_id):
        """
        Bulk enroll students in a class.
        
        Request body:
        {
            "students": [1, 2, 3, ...]  // Array of student IDs
        }
        """
        # Add class_id to request data
        data = {
            'enrolled_class': class_id,
            'students': request.data.get('students', [])
        }
        
        serializer = BulkEnrollmentSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Create enrollments
        enrolled_class = serializer.validated_data['enrolled_class']
        students = serializer.validated_data['students']
        
        enrollments = []
        for student in students:
            enrollments.append(
                Enrollment(
                    enrolled_class=enrolled_class,
                    student=student,
                    enrolled_by=request.user
                )
            )
        
        # Bulk create
        created_enrollments = Enrollment.objects.bulk_create(enrollments)
        
        return Response({
            'message': f'Successfully enrolled {len(created_enrollments)} students',
            'enrolled_count': len(created_enrollments),
            'class_id': class_id
        }, status=status.HTTP_201_CREATED)


class AttendanceListCreateAPIView(generics.ListCreateAPIView):
    """
    API endpoint for listing and creating attendance records.
    
    GET: List all attendance records for a specific class
    POST: Record attendance for a student (admin/faculty only)
    """
    serializer_class = AttendanceSerializer
    
    def get_permissions(self):
        """Admin/Faculty only for POST, authenticated for GET."""
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """Get attendance records for a specific class, optionally filtered by date."""
        class_id = self.kwargs.get('class_id')
        queryset = Attendance.objects.filter(class_instance_id=class_id).select_related(
            'student', 'class_instance', 'updated_by'
        )
        
        # Optional date filter
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        # Optional student filter
        student_id = self.request.query_params.get('student')
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        return queryset
    
    def get_serializer_class(self):
        """Use create/update serializer for POST."""
        if self.request.method == 'POST':
            return AttendanceCreateUpdateSerializer
        return AttendanceSerializer


class AttendanceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, or deleting a specific attendance record.
    
    GET: Retrieve attendance details
    PUT/PATCH: Update attendance record (admin/faculty only)
    DELETE: Delete attendance record (admin only)
    """
    queryset = Attendance.objects.select_related('student', 'class_instance', 'updated_by')
    serializer_class = AttendanceSerializer
    
    def get_permissions(self):
        """Admin only for DELETE, admin/faculty for PUT/PATCH, authenticated for GET."""
        if self.request.method == 'DELETE':
            return [IsAdminUser()]
        elif self.request.method in ['PUT', 'PATCH']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Use create/update serializer for PUT/PATCH."""
        if self.request.method in ['PUT', 'PATCH']:
            return AttendanceCreateUpdateSerializer
        return AttendanceSerializer


class BulkAttendanceAPIView(APIView):
    """
    API endpoint for bulk recording attendance for multiple students.
    
    POST: Record attendance for multiple students at once (admin/faculty only)
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, class_id):
        """
        Bulk record attendance for students.
        
        Request body:
        {
            "date": "2025-12-03",
            "attendance_records": [
                {"student": 1, "status": "present", "remarks": ""},
                {"student": 2, "status": "absent", "remarks": "Sick"},
                ...
            ]
        }
        """
        # Add class_id to request data
        data = {
            'class_instance': class_id,
            'date': request.data.get('date'),
            'attendance_records': request.data.get('attendance_records', [])
        }
        
        serializer = BulkAttendanceSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Process attendance records
        class_instance = serializer.validated_data['class_instance']
        date = serializer.validated_data['date']
        attendance_records = serializer.validated_data['attendance_records']
        
        # Update or create attendance records
        created_count = 0
        updated_count = 0
        
        for record in attendance_records:
            student_id = int(record['student'])
            status = record['status']
            remarks = record.get('remarks', '')
            
            attendance, created = Attendance.objects.update_or_create(
                class_instance=class_instance,
                student_id=student_id,
                date=date,
                defaults={
                    'status': status,
                    'remarks': remarks,
                    'updated_by': request.user
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        return Response({
            'message': f'Attendance recorded successfully',
            'created': created_count,
            'updated': updated_count,
            'total': created_count + updated_count,
            'class_id': class_id,
            'date': date
        }, status=status.HTTP_201_CREATED)


class CurriculumCourseListAPIView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = CurriculumCourseSerializer
    queryset = Curriculum.objects.all()

class ScheduleBlockViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ScheduleBlock
    - Students: Can only access their own blocks
    - Faculty/Admin: Can access all blocks (with filtering capabilities)
     Includes nested schedule_entries with full entry details
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN/FACULTY: Full access
        if user.is_staff or user.is_superuser or hasattr(user, 'facultyprofile'):
            queryset = ScheduleBlock.objects.all()

            # Allow filtering by student
            student_id = self.request.query_params.get('student_id')
            if student_id:
                queryset = queryset.filter(user_id=student_id)

            return queryset

        # STUDENT: Restricted to own data
        elif hasattr(user, 'studentprofile'):
            return ScheduleBlock.objects.filter(user_id=user.studentprofile)

        # DEFAULT: No access
        else:
            return ScheduleBlock.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleBlockCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScheduleBlockUpdateSerializer
        return ScheduleBlockSerializer

    def perform_create(self, serializer): #This will perhaps be used when a new class is created
        user = self.request.user

        # Students: auto-assign their student profile. Student is VIEW ONLY. DO NOT USE THIS for student views
        if hasattr(user, 'studentprofile'):
            # serializer.save(user_id=user.studentprofile)
            pass
        # Faculty/Admin: can specify any user_id in the request
        elif user.is_staff or user.is_superuser or hasattr(user, 'facultyprofile'):
            serializer.save()
        else:
            raise serializers.ValidationError("User doesn't have appropriate permissions")
    # Above destroy method is commented out to prevent accidental deletions, not to mention it's not really usefule for a viewing intention right now lol

class ScheduleEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for ScheduleEntry
    - Students: Can only access entries in their own blocks
    - Faculty/Admin: Can access all entries
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # ADMIN/FACULTY: Full access
        if user.is_staff or user.is_superuser or hasattr(user, 'facultyprofile'):
            queryset = ScheduleEntry.objects.all()

            # Allow faculty/admin to filter by student if needed
            student_id = self.request.query_params.get('student_id')
            if student_id:
                queryset = queryset.filter(schedule_block_id__user_id=student_id)

            return queryset

        # STUDENT: Restricted to own data
        elif hasattr(user, 'studentprofile'):
            user_blocks = ScheduleBlock.objects.filter(user_id=user.studentprofile)

            block_id = self.request.query_params.get('block_id')
            if block_id:
                if user_blocks.filter(id=block_id).exists():
                    return ScheduleEntry.objects.filter(schedule_block_id=block_id)
                else:
                    return ScheduleEntry.objects.none()

            return ScheduleEntry.objects.filter(schedule_block_id__in=user_blocks)

        # DEFAULT: No access
        else:
            return ScheduleEntry.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return ScheduleEntryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ScheduleEntryUpdateSerializer
        return ScheduleEntrySerializer


    def perform_create(self, serializer):
        """
        Never use this in the student views, only for faculty/admin
        """

        user = self.request.user
        schedule_block = serializer.validated_data.get('schedule_block_id')

        # Students can only create in their own blocks
        if hasattr(user, 'studentprofile'):
            if schedule_block.user_id != user.studentprofile:
                raise serializers.ValidationError("You can only create entries in your own schedule blocks")

        # Faculty/Admin can create in any block without restrictions
        serializer.save()



def is_faculty_of_class(user, class_id):
    """Check if user is the faculty assigned to the class"""
    if not hasattr(user, 'facultyprofile'):
        return False
    return Class.objects.filter(
        id=class_id, 
        faculty=user.facultyprofile
    ).exists()


def is_student_in_class(user, class_id):
    """Check if user is enrolled in the class"""
    if not hasattr(user, 'studentprofile'):
        return False
    return Enrollment.objects.filter(
        enrolled_class_id=class_id,
        student=user.studentprofile
    ).exists()


class GradingRubricListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all grading rubrics for a class
    POST: Create a new grading rubric with components
    
    URL: /api/academics/classes/{class_id}/grading-rubrics/
    
    Faculty only for POST, anyone authenticated for GET.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        return GradingRubric.objects.filter(
            class_instance_id=class_id
        ).prefetch_related('components')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return GradingRubricCreateSerializer
        return GradingRubricSerializer
    
    def perform_create(self, serializer):
        """Only faculty can create rubrics"""
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            raise PermissionError("Only faculty can create grading rubrics.")
        
        serializer.save()


class GradingRubricDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific grading rubric
    PUT/PATCH: Update a grading rubric
    DELETE: Delete a grading rubric
    
    URL: /api/academics/grading-rubrics/{rubric_id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = GradingRubric.objects.all().prefetch_related('components')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return GradingRubricUpdateSerializer
        return GradingRubricSerializer
    
    def perform_update(self, serializer):
        """Only faculty can update rubrics"""
        rubric = self.get_object()
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, rubric.class_instance.id)):
            raise PermissionError("Only faculty can update grading rubrics.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only faculty can delete rubrics"""
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, instance.class_instance.id)):
            raise PermissionError("Only faculty can delete grading rubrics.")
        
        instance.delete()



class RubricComponentListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all components for a rubric
    POST: Create a new component for a rubric
    
    URL: /api/academics/grading-rubrics/{rubric_id}/components/
    """
    permission_classes = [IsAuthenticated]
    serializer_class = RubricComponentCreateUpdateSerializer
    
    def get_queryset(self):
        rubric_id = self.kwargs['rubric_id']
        return RubricComponent.objects.filter(rubric_id=rubric_id)
    
    def perform_create(self, serializer):
        """Only faculty can create components"""
        rubric_id = self.kwargs['rubric_id']
        rubric = get_object_or_404(GradingRubric, id=rubric_id)
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, rubric.class_instance.id)):
            raise PermissionError("Only faculty can create rubric components.")
        
        serializer.save(rubric=rubric)


class RubricComponentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific component
    PUT/PATCH: Update a component
    DELETE: Delete a component
    
    URL: /api/academics/rubric-components/{component_id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = RubricComponent.objects.all()
    serializer_class = RubricComponentCreateUpdateSerializer
    
    def perform_update(self, serializer):
        """Only faculty can update components"""
        component = self.get_object()
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, component.rubric.class_instance.id)):
            raise PermissionError("Only faculty can update components.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only faculty can delete components"""
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, instance.rubric.class_instance.id)):
            raise PermissionError("Only faculty can delete components.")
        
        instance.delete()



class TopicListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all topics for a class
    POST: Create a new topic
    
    URL: /api/academics/classes/{class_id}/topics/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        return Topic.objects.filter(class_instance_id=class_id)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TopicCreateUpdateSerializer
        return TopicSerializer
    
    def perform_create(self, serializer):
        """Only faculty can create topics"""
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            raise PermissionError("Only faculty can create topics.")
        
        serializer.save()


class TopicDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific topic
    PUT/PATCH: Update a topic
    DELETE: Delete a topic
    
    URL: /api/academics/topics/{topic_id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = Topic.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TopicCreateUpdateSerializer
        return TopicSerializer
    
    def perform_update(self, serializer):
        """Only faculty can update topics"""
        topic = self.get_object()
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, topic.class_instance.id)):
            raise PermissionError("Only faculty can update topics.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only faculty can delete topics"""
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, instance.class_instance.id)):
            raise PermissionError("Only faculty can delete topics.")
        
        instance.delete()

class MaterialListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all materials for a class
    POST: Create a new material
    
    URL: /api/academics/classes/{class_id}/materials/
    
    Students can only see published materials.
    Faculty can see all materials.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        queryset = Material.objects.filter(class_instance_id=class_id)
        
        # Students only see published materials
        if hasattr(user, 'studentprofile') and not user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        return queryset.select_related('topic', 'created_by')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MaterialCreateUpdateSerializer
        elif self.request.method == 'GET' and self.request.query_params.get('list_view'):
            return MaterialListSerializer
        return MaterialSerializer
    
    def perform_create(self, serializer):
        """Only faculty can create materials"""
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            raise PermissionError("Only faculty can create materials.")
        
        serializer.save(created_by=user)


class MaterialDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific material
    PUT/PATCH: Update a material
    DELETE: Delete a material
    
    URL: /api/academics/materials/{material_id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = Material.objects.all().select_related('topic', 'created_by')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MaterialCreateUpdateSerializer
        return MaterialSerializer
    
    def get_object(self):
        """Students can only access published materials"""
        obj = super().get_object()
        user = self.request.user
        
        if hasattr(user, 'studentprofile') and not user.is_staff:
            if not obj.is_published:
                raise PermissionError("Material not published yet.")
        
        return obj
    
    def perform_update(self, serializer):
        """Only faculty can update materials"""
        material = self.get_object()
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, material.class_instance.id)):
            raise PermissionError("Only faculty can update materials.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only faculty can delete materials"""
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, instance.class_instance.id)):
            raise PermissionError("Only faculty can delete materials.")
        
        instance.delete()


class AssessmentListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all assessments for a class
    POST: Create a new assessment
    
    URL: /api/academics/classes/{class_id}/assessments/
    
    Students can only see published assessments.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        queryset = Assessment.objects.filter(class_instance_id=class_id)
        
        # Students only see published assessments
        if hasattr(user, 'studentprofile') and not user.is_staff:
            queryset = queryset.filter(is_published=True)
        
        return queryset.select_related(
            'topic', 'rubric_component', 'created_by'
        )
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return AssessmentCreateUpdateSerializer
        elif self.request.method == 'GET' and self.request.query_params.get('list_view'):
            return AssessmentListSerializer
        return AssessmentSerializer
    
    def perform_create(self, serializer):
        """Only faculty can create assessments"""
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            raise PermissionError("Only faculty can create assessments.")
        
        serializer.save(created_by=user)


class AssessmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific assessment
    PUT/PATCH: Update an assessment
    DELETE: Delete an assessment
    
    URL: /api/academics/assessments/{assessment_id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = Assessment.objects.all().select_related(
        'topic', 'rubric_component', 'created_by'
    )
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return AssessmentCreateUpdateSerializer
        return AssessmentSerializer
    
    def get_object(self):
        """Students can only access published assessments"""
        obj = super().get_object()
        user = self.request.user
        
        if hasattr(user, 'studentprofile') and not user.is_staff:
            if not obj.is_published:
                raise PermissionError("Assessment not published yet.")
        
        return obj
    
    def perform_update(self, serializer):
        """Only faculty can update assessments"""
        assessment = self.get_object()
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, assessment.class_instance.id)):
            raise PermissionError("Only faculty can update assessments.")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """Only faculty can delete assessments"""
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, instance.class_instance.id)):
            raise PermissionError("Only faculty can delete assessments.")
        
        instance.delete()




class ScoreListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all scores for a class or assessment
    POST: Create a new score
    
    URL: /api/academics/classes/{class_id}/scores/
    Optional query params: ?assessment_id=X&student_id=Y&published_only=true
    
    Students can only see their own published scores.
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        queryset = Score.objects.filter(class_instance_id=class_id)
        
        # Filter by assessment if provided
        assessment_id = self.request.query_params.get('assessment_id')
        if assessment_id:
            queryset = queryset.filter(assessment_id=assessment_id)
        
        # Filter by student if provided (faculty/admin only)
        student_id = self.request.query_params.get('student_id')
        if student_id and (user.is_staff or is_faculty_of_class(user, class_id)):
            queryset = queryset.filter(student_id=student_id)
        
        # Students only see their own published scores
        if hasattr(user, 'studentprofile') and not user.is_staff:
            queryset = queryset.filter(
                student=user.studentprofile,
                is_published=True
            )
        
        # Filter published only if requested
        if self.request.query_params.get('published_only') == 'true':
            queryset = queryset.filter(is_published=True)
        
        return queryset.select_related('student', 'assessment', 'uploaded_by')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ScoreCreateUpdateSerializer
        elif self.request.method == 'GET' and self.request.query_params.get('list_view'):
            return ScoreListSerializer
        return ScoreSerializer
    
    def perform_create(self, serializer):
        """Only faculty can create scores"""
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            raise PermissionError("Only faculty can create scores.")
        
        serializer.save(uploaded_by=user)


class ScoreDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific score
    PUT/PATCH: Update a score
    DELETE: Delete a score
    
    URL: /api/academics/scores/{score_id}/
    """
    permission_classes = [IsAuthenticated]
    queryset = Score.objects.all().select_related('student', 'assessment', 'uploaded_by')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ScoreCreateUpdateSerializer
        return ScoreSerializer
    
    def get_object(self):
        """Students can only access their own published scores"""
        obj = super().get_object()
        user = self.request.user
        
        if hasattr(user, 'studentprofile') and not user.is_staff:
            if obj.student != user.studentprofile or not obj.is_published:
                raise PermissionError("You can only view your own published scores.")
        
        return obj
    
    def perform_update(self, serializer):
        """Only faculty can update scores"""
        score = self.get_object()
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, score.class_instance.id)):
            raise PermissionError("Only faculty can update scores.")
        
        serializer.save(uploaded_by=user)
    
    def perform_destroy(self, instance):
        """Only faculty can delete scores"""
        user = self.request.user
        
        if not (user.is_staff or is_faculty_of_class(user, instance.class_instance.id)):
            raise PermissionError("Only faculty can delete scores.")
        
        instance.delete()


class BulkScoreCreateAPIView(APIView):
    """
    POST: Bulk create/update scores for all enrolled students in a class.
    Used when faculty sets the same score for all students (bulk input feature).
    
    URL: /api/academics/classes/{class_id}/scores/bulk-create/
    
    Request body:
    {
        "assessment_id": 1,
        "points": 35,
        "is_published": false
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, class_id):
        user = request.user
        
        # Permission check
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            return Response(
                {"error": "Only faculty can bulk create scores."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate input
        serializer = BulkScoreCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        assessment = serializer.validated_data['assessment']
        points = serializer.validated_data['points']
        is_published = serializer.validated_data['is_published']
        
        # Verify assessment belongs to this class
        if assessment.class_instance.id != class_id:
            return Response(
                {"error": "Assessment does not belong to this class."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get all enrolled students
        enrollments = Enrollment.objects.filter(enrolled_class_id=class_id)
        
        # Bulk create/update scores
        scores_to_create = []
        scores_to_update = []
        
        for enrollment in enrollments:
            student = enrollment.student
            
            # Check if score already exists
            try:
                existing_score = Score.objects.get(
                    student=student,
                    assessment=assessment
                )
                existing_score.points = points
                existing_score.is_published = is_published
                existing_score.uploaded_by = user
                scores_to_update.append(existing_score)
            except Score.DoesNotExist:
                scores_to_create.append(
                    Score(
                        class_instance_id=class_id,
                        student=student,
                        assessment=assessment,
                        points=points,
                        is_published=is_published,
                        uploaded_by=user
                    )
                )
        
        # Perform bulk operations
        if scores_to_create:
            Score.objects.bulk_create(scores_to_create)
        
        if scores_to_update:
            Score.objects.bulk_update(
                scores_to_update, 
                ['points', 'is_published', 'uploaded_by', 'updated_at']
            )
        
        return Response(
            {
                "message": f"Bulk created/updated scores for {len(scores_to_create) + len(scores_to_update)} students.",
                "created": len(scores_to_create),
                "updated": len(scores_to_update)
            },
            status=status.HTTP_200_OK
        )


class BulkScoreUploadAPIView(APIView):
    """
    POST: Bulk upload (publish) all scores for an assessment.
    Marks all scores for an assessment as published (visible to students).
    
    URL: /api/academics/classes/{class_id}/scores/bulk-upload/
    
    Request body:
    {
        "assessment_id": 1
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, class_id):
        user = request.user
        
        # Permission check
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            return Response(
                {"error": "Only faculty can bulk upload scores."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate input
        serializer = BulkScoreUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        assessment_id = serializer.validated_data['assessment_id']
        
        # Verify assessment belongs to this class
        assessment = get_object_or_404(Assessment, id=assessment_id)
        if assessment.class_instance.id != class_id:
            return Response(
                {"error": "Assessment does not belong to this class."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Bulk update all scores for this assessment
        updated_count = Score.objects.filter(
            class_instance_id=class_id,
            assessment_id=assessment_id
        ).update(is_published=True)
        
        return Response(
            {
                "message": f"Published {updated_count} scores for assessment '{assessment.title}'.",
                "count": updated_count
            },
            status=status.HTTP_200_OK
        )


class StudentGradesSummaryAPIView(APIView):
    """
    GET: Retrieve comprehensive grade summary for a student in a class.
    Calculates midterm, final term, and overall grades based on rubrics.
    
    URL: /api/academics/classes/{class_id}/students/{student_id}/grades/
    
    Students can only access their own grades.
    Faculty can access any student's grades.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, class_id, student_id):
        user = request.user
        
        # Permission check
        if hasattr(user, 'studentprofile'):
            # Students can only view their own grades
            if str(user.studentprofile.id) != str(student_id):
                return Response(
                    {"error": "You can only view your own grades."},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not (user.is_staff or is_faculty_of_class(user, class_id)):
            return Response(
                {"error": "You don't have permission to view these grades."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get class and student
        class_instance = get_object_or_404(Class, id=class_id)
        from ..Users.models import StudentProfile
        student = get_object_or_404(StudentProfile, id=student_id)
        
        # Verify student is enrolled in this class
        if not Enrollment.objects.filter(
            enrolled_class=class_instance,
            student=student
        ).exists():
            return Response(
                {"error": "Student is not enrolled in this class."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get rubrics for this class
        rubrics = GradingRubric.objects.filter(
            class_instance=class_instance
        ).prefetch_related('components__assessments__scores')
        
        # Calculate grades
        grades_data = self._calculate_grades(student, rubrics)
        
        # Prepare response
        response_data = {
            'student_id': student.id,
            'student_name': f"{student.user.last_name}, {student.user.first_name}",
            'class_id': class_instance.id,
            'class_name': class_instance.course.title,
            **grades_data
        }
        
        serializer = StudentGradesSummarySerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
    def _calculate_grades(self, student, rubrics):
        """
        Calculate comprehensive grades for a student.
        Returns midterm, final term, and overall grades with component breakdowns.
        """
        midterm_rubric = None
        final_rubric = None
        
        for rubric in rubrics:
            if rubric.academic_period == 'midterm':
                midterm_rubric = rubric
            elif rubric.academic_period == 'finals':
                final_rubric = rubric
        
        # Calculate midterm grade
        midterm_data = self._calculate_term_grade(student, midterm_rubric) if midterm_rubric else {
            'grade': Decimal('0.00'),
            'components': {}
        }
        
        # Calculate final term grade
        final_data = self._calculate_term_grade(student, final_rubric) if final_rubric else {
            'grade': Decimal('0.00'),
            'components': {}
        }
        
        # Calculate overall grade
        midterm_contribution = Decimal('0.00')
        final_contribution = Decimal('0.00')
        
        if midterm_rubric:
            midterm_contribution = (midterm_data['grade'] * midterm_rubric.term_percentage) / Decimal('100.00')
        
        if final_rubric:
            final_contribution = (final_data['grade'] * final_rubric.term_percentage) / Decimal('100.00')
        
        final_grade = midterm_contribution + final_contribution
        
        return {
            'midterm_grade': midterm_data['grade'],
            'final_term_grade': final_data['grade'],
            'final_grade': final_grade,
            'midterm_components': midterm_data['components'],
            'final_components': final_data['components']
        }
    
    def _calculate_term_grade(self, student, rubric):
        """
        Calculate grade for a single term (midterm or finals).
        Returns the term grade and component breakdown.
        """
        if not rubric:
            return {'grade': Decimal('0.00'), 'components': {}}
        
        components_data = {}
        term_grade = Decimal('0.00')
        
        for component in rubric.components.all():
            # Get all assessments for this component
            assessments = component.assessments.all()
            
            if not assessments:
                components_data[component.name] = {
                    'percentage': float(component.percentage),
                    'average': 0.00,
                    'assessments': []
                }
                continue
            
            # Calculate component average
            total_score = Decimal('0.00')
            total_max = Decimal('0.00')
            assessment_details = []
            
            for assessment in assessments:
                # Get student's score (only published if student is viewing)
                try:
                    score = Score.objects.get(
                        student=student,
                        assessment=assessment,
                        is_published=True  # Only count published scores
                    )
                    total_score += Decimal(str(score.points))
                    total_max += Decimal(str(assessment.max_points))
                    
                    assessment_details.append({
                        'title': assessment.title,
                        'points': float(score.points),
                        'max_points': assessment.max_points,
                        'percentage': float(score.percentage)
                    })
                except Score.DoesNotExist:
                    # No score yet, treat as 0
                    total_max += Decimal(str(assessment.max_points))
                    assessment_details.append({
                        'title': assessment.title,
                        'points': 0,
                        'max_points': assessment.max_points,
                        'percentage': 0.00
                    })
            
            # Calculate component average percentage
            if total_max > 0:
                component_avg = (total_score / total_max) * Decimal('100.00')
            else:
                component_avg = Decimal('0.00')
            
            # Calculate contribution to term grade
            component_contribution = (component_avg * component.percentage) / Decimal('100.00')
            term_grade += component_contribution
            
            components_data[component.name] = {
                'percentage': float(component.percentage),
                'average': float(component_avg),
                'contribution': float(component_contribution),
                'assessments': assessment_details
            }
        
        return {
            'grade': term_grade,
            'components': components_data
        }



class ClassStudentsListAPIView(generics.ListAPIView):
    """
    GET: List all students enrolled in a class.
    Used by faculty to see who's in their class.
    
    URL: /api/academics/classes/{class_id}/students/
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        class_id = self.kwargs['class_id']
        user = self.request.user
        
        # Only faculty and admin can view student list
        if not (user.is_staff or is_faculty_of_class(user, class_id)):
            return Enrollment.objects.none()
        
        return Enrollment.objects.filter(
            enrolled_class_id=class_id
        ).select_related('student__user')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        students_data = []
        for enrollment in queryset:
            student = enrollment.student
            students_data.append({
                'id': student.id,
                'institutional_id': student.institutional_id,
                'username': student.user.username,
                'first_name': student.user.first_name,
                'last_name': student.user.last_name,
                'name': f"{student.user.last_name}, {student.user.first_name}",
                'email': student.user.email,
                'enrolled_at': enrollment.enrolled_at
            })
        
        return Response({
            'count': len(students_data),
            'students': students_data
        }, status=status.HTTP_200_OK)