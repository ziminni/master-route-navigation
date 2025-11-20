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

urlpatterns = [
    path('api/', include(router.urls)),
]