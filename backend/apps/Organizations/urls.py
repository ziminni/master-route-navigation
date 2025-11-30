from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'event-types', views.EventTypeViewSet)
router.register(r'event-schedule-blocks', views.EventScheduleBlockViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'event-schedules', views.EventScheduleViewSet)
router.register(r'event-attendance', views.EventAttendanceViewSet)
router.register(r'event-approvals', views.EventApprovalViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

# ENDPOINT DOCUMENTATION
# Warning: Some of these endpoints may have incorrect access restrictions. We won't have time to fix them all now.
# Use only wwhat makes sense for your use case and double-check permissions in views.py 
# Event Types Endpoints
# Quick Login Just in case you need le quick login in postman to test the endpoints and get your 
# frontend connections in order.
# This assumes you ran the mock data script to create users including org_officer1
# If you haven't yet, run python manage.py runscript mock_data_create_events
# The mock data script assumes you wiped the database clean first and then migrated fresh>

# http://localhost:8000/api/users/login/api/
# body: {
#   "identifier": "org_officer1",
#   "password": "password123"
# }
# Headers: Key :Content-Type Value application/json>
#Then save the token and use it wherever needed, AI be your friend on figuring that out.
# Remember all endpoints here starts with http://localhost:8000/api/organizations/ 

# GET    /event-types/           - List all event types (Authenticated)
# POST   /event-types/           - Create new event type (Authenticated)
# GET    /event-types/{id}/      - Retrieve specific event type (Authenticated)
# PUT    /event-types/{id}/      - Update event type (Authenticated)
# PATCH  /event-types/{id}/      - Partial update event type (Authenticated)
# DELETE /event-types/{id}/      - Delete event type (Authenticated)

# Event Schedule Blocks Endpoints

# GET    /event-schedule-blocks/           - List all schedule blocks (Authenticated)
# POST   /event-schedule-blocks/           - Create new schedule block (Org Officer)
# GET    /event-schedule-blocks/{id}/      - Retrieve specific schedule block with nested events (Authenticated)
# PUT    /event-schedule-blocks/{id}/      - Update schedule block (Org Officer)
# PATCH  /event-schedule-blocks/{id}/      - Partial update schedule block (Org Officer)
# DELETE /event-schedule-blocks/{id}/      - Delete schedule block (Org Officer)

# Events Endpoints (Main CRUD)

# GET    /events/           - List events (Role-based filtering)
# POST   /events/           - Create new event (Org Officer)
# GET    /events/{id}/      - Retrieve specific event with nested schedules, approvals, attendance (Authenticated)
# PUT    /events/{id}/      - Update event (Org Officer)
# PATCH  /events/{id}/      - Partial update event (Org Officer)
# DELETE /events/{id}/      - Delete event (Currently Authenticated - consider restricting)

# Events Custom Actions

# PATCH  /events/{id}/update_status/    - Update event status (Faculty)
# POST   /events/{id}/approve/          - Approve event & create approval record (Faculty)
# POST   /events/{id}/reject/           - Reject event (Faculty)
# GET    /events/current_upcoming/      - Get current & upcoming approved events (Students)

# Event Schedules Endpoints

# GET    /event-schedules/           - List all event schedules (Authenticated)
# POST   /event-schedules/           - Create new event schedule (Org Officer)
# GET    /event-schedules/{id}/      - Retrieve specific event schedule (Authenticated)
# PUT    /event-schedules/{id}/      - Update event schedule (Org Officer)
# PATCH  /event-schedules/{id}/      - Partial update event schedule (Org Officer)
# DELETE /event-schedules/{id}/      - Delete event schedule (Org Officer)

# Event Attendance Endpoints

# GET    /event-attendance/           - List attendance records (Role-based: students see own, faculty see all)
# POST   /event-attendance/           - Create attendance record (Student - for applying to events)
# GET    /event-attendance/{id}/      - Retrieve specific attendance record (Authenticated)
# PUT    /event-attendance/{id}/      - Update attendance record (Authenticated)
# PATCH  /event-attendance/{id}/      - Partial update attendance record (Authenticated)
# DELETE /event-attendance/{id}/      - Delete attendance record (Authenticated)

# Event Approvals Endpoints

# GET    /event-approvals/           - List all event approvals (Authenticated)
# POST   /event-approvals/           - Create event approval (Faculty)
# GET    /event-approvals/{id}/      - Retrieve specific approval (Authenticated)
# PUT    /event-approvals/{id}/      - Update approval (Authenticated)
# PATCH  /event-approvals/{id}/      - Partial update approval (Authenticated)
# DELETE /event-approvals/{id}/      - Delete approval (Authenticated)

