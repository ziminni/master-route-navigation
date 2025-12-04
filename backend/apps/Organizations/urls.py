from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'event-types', views.EventTypeViewSet)
router.register(r'event-schedule-blocks', views.EventScheduleBlockViewSet)
router.register(r'event-schedules', views.EventScheduleViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'event-attendance', views.EventAttendanceViewSet)
router.register(r'event-approvals', views.EventApprovalViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]

# event schedule endpoints:
# GET/POST /api/events/ - List/create events
# GET/PUT/DELETE /api/events/{id}/ - Retrieve/update/delete event
# POST /api/events/{id}/approve_event/ - Approve an event
# GET /api/events/{id}/attendance/ - Get event attendance
# POST /api/events/{id}/update_status/ - Update event status
# GET /api/event-attendance/by_student/?student_id=X - Get student attendance
# GET /api/event-attendance/by_event/?event_id=X - Get event attendance