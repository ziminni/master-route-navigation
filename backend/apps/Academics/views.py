from django.shortcuts import render

# views.py
from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import ScheduleBlock, ScheduleEntry, Semester, Enrollment, Class
from django.db.models import Prefetch
from apps.Users.models import StudentProfile, FacultyProfile
from .serializers import *
from django.shortcuts import get_object_or_404

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
        
        
        
        
#MODULE 3
class StudentScheduleViewSet(viewsets.ViewSet):
    """
    ViewSet for retrieving student schedules
    """
    
    @action(detail=True, methods=['get'], url_path='schedule')
    def get_student_schedule(self, request, pk=None):
        """
        Get individual student's schedule
        pk: Student ID
        """
        try:
            # Get the student
            student = StudentProfile.objects.get(pk=pk)
            #TODO: change this to allow getting schedule for specific semester
            # Get current active semester
            from .models import Semester
            active_semester = Semester.objects.filter(is_active=True).first()
            
            if not active_semester:
                return Response(
                    {"error": "No active semester found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get all enrollments for this student in active semester
            enrollments = Enrollment.objects.filter(
                student=student,
                enrolled_class__semester=active_semester
            ).select_related(
                'enrolled_class',
                'enrolled_class__course',
                'enrolled_class__section',
                'enrolled_class__schedule_block'
            ).prefetch_related(
                Prefetch(
                    'enrolled_class__schedule_block__scheduleentry_set',
                    queryset=ScheduleEntry.objects.all()
                )
            )
            
            schedule_data = []
            
            for enrollment in enrollments:
                class_obj = enrollment.enrolled_class
                schedule_block = class_obj.schedule_block
                
                if schedule_block:
                    # Get all schedule entries for this block
                    schedule_entries = schedule_block.scheduleentry_set.all()
                    
                    for entry in schedule_entries:
                        schedule_data.append({
                            'class_id': class_obj.id,
                            'course_code': class_obj.course.code,
                            'course_title': class_obj.course.title,
                            'section_name': class_obj.section.name,
                            'class_type': class_obj.section.get_type_display(),
                            'faculty': f"{class_obj.faculty.user.first_name} {class_obj.faculty.user.last_name}" if class_obj.faculty else "TBA",
                            'schedule_entry': {
                                'id': entry.id,
                                'entry_name': entry.entry_name,
                                'additional_context': entry.additional_context,
                                'day_of_week': entry.get_day_of_week_display(),
                                'day_of_week_code': entry.day_of_week,
                                'start_time': entry.start_time,
                                'end_time': entry.end_time
                            }
                        })
            
            return Response({
                'student_id': student.id,
                'student_name': f"{student.user.first_name} {student.user.last_name}",
                'semester': f"{active_semester.term} {active_semester.academic_year.start_date.year}-{active_semester.academic_year.end_date.year}",
                'schedule': schedule_data
            })
            
        except StudentProfile.DoesNotExist:
            return Response(
                {"error": "Student not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='my-schedule')
    def get_my_schedule(self, request):
        """
        Get schedule for the currently authenticated student
        """
        if not hasattr(request.user, 'studentprofile'):
            return Response(
                {"error": "User is not a student"}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        student = request.user.studentprofile
        return self.get_student_schedule(request, pk=student.id)
    
# Example response:
# {
#     "student_id": 1,
#     "student_name": "John Doe",
#     "semester": "First Semester 2023-2024",
#     "schedule": [
#         {
#             "class_id": 1,
#             "course_code": "CS101",
#             "course_title": "Introduction to Programming",
#             "section_name": "A",
#             "class_type": "Lecture",
#             "faculty": "Dr. Smith",
#             "schedule_entry": {
#                 "id": 1,
#                 "entry_name": "CS101 Lecture",
#                 "additional_context": "Room 101",
#                 "day_of_week": "Monday",
#                 "day_of_week_code": "mon",
#                 "start_time": "2023-09-01T09:00:00Z",
#                 "end_time": "2023-09-01T10:30:00Z"
#             }
#         }
#     ]
# }