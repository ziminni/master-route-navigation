from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduleBlockViewSet, ScheduleEntryViewSet , StudentScheduleViewSet, EnrollmentViewSet

router = DefaultRouter()
router.register(r'schedule-blocks', ScheduleBlockViewSet, basename='scheduleblock')
router.register(r'schedule-entries', ScheduleEntryViewSet, basename='scheduleentry')
router.register(r'student-schedules', StudentScheduleViewSet, basename='student-schedule')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')


# Funny notes for frontend in mod 3 and perhaps other modules, so that we won't forget later on what endpoints are available here:
# GET /api/schedule-blocks/ - List all accessible schedule blocks
# POST /api/schedule-blocks/ - Create a new schedule block
# GET /api/schedule-blocks/{id}/ - Get specific schedule block
# PUT /api/schedule-blocks/{id}/ - Update entire schedule block
# PATCH /api/schedule-blocks/{id}/ - Partial update schedule block
# DELETE /api/schedule-blocks/{id}/ - Delete schedule block
# GET /api/student-schedules/{student_id}/schedule/ - Retrieve schedule for a specific student by ID
# GET /api/student-schedules/my-schedule/ - Retrieve schedule for the currently authenticated student
# GET /api/enrollments/ - List all enrollment records
# POST /api/enrollments/ - Create a new enrollment record
# GET /api/enrollments/{id}/ - Retrieve details of a specific enrollment
# PUT /api/enrollments/{id}/ - Complete update of an enrollment record
# PATCH /api/enrollments/{id}/ - Partial update of an enrollment record
# DELETE /api/enrollments/{id}/ - Delete an enrollment record
# GET /api/enrollments/student/{student_id}/schedule/ - Get student schedule through enrollment relationships
urlpatterns = [
    path('api/', include(router.urls)),
]