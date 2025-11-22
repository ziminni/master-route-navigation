from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduleBlockViewSet, ScheduleEntryViewSet, SemesterViewSet, CurriculumViewSet, \
    ActiveSemesterAPIView

router = DefaultRouter()
router.register(r'schedule-blocks', ScheduleBlockViewSet, basename='scheduleblock')
router.register(r'schedule-entries', ScheduleEntryViewSet, basename='scheduleentry')


# Funny notes about endpoints for frontend in mod 3 and perhaps other modules, so that we won't forget later on what endpoints are available here:
# GET /api/schedule-blocks/ - List all accessible schedule blocks
# POST /api/schedule-blocks/ - Create a new schedule block
# GET /api/schedule-blocks/{id}/ - Get specific schedule block
# PUT /api/schedule-blocks/{id}/ - Update entire schedule block, As to how to update it exactly. 
#                                   Some wizardry from the frontend is required to comfortably update it efficiently
# PATCH /api/schedule-blocks/{id}/ - Partial update schedule block
# DELETE /api/schedule-blocks/{id}/ - Delete schedule block


# GET /api/schedule-entries/ - List all accessible schedule entries
# POST /api/schedule-entries/ - Create a new schedule entry
# GET /api/schedule-entries/{id}/ - Get specific schedule entry
# PUT /api/schedule-entries/{id}/ - Update entire schedule entry
# PATCH /api/schedule-entries/{id}/ - Partial update schedule entry
# DELETE /api/schedule-entries/{id}/ - Delete schedule entry

router.register(r'semesters', SemesterViewSet, basename='semester')
# /api/semesters/
# GET - retrieves a list of semesters
# POST - create a new semester

# /api/semesters/{id}/
# GET - retrieves a single semester
# PUT - update entire semester object
# PATCH - partial update semester object
# DELETE - delete semester object
router.register(r'curriculums', CurriculumViewSet, basename='curriculum')


urlpatterns = [
    path('semesters/active/', ActiveSemesterAPIView.as_view(), name='active-semester-retrieve-api-view'),
    path('', include(router.urls)),
]