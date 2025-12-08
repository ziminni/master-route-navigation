from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
# router.register(r'event-types', views.EventTypeViewSet)
# router.register(r'event-schedule-blocks', views.EventScheduleBlockViewSet)
# router.register(r'event-schedules', views.EventScheduleViewSet)
# router.register(r'events', views.EventViewSet)
# router.register(r'event-attendance', views.EventAttendanceViewSet)
# router.register(r'event-approvals', views.EventApprovalViewSet)

# urlpatterns = [
#     path('api/', include(router.urls)),
# ]

# event schedule endpoints:
# GET/POST /api/events/ - List/create events
# GET/PUT/DELETE /api/events/{id}/ - Retrieve/update/delete event
# POST /api/events/{id}/approve_event/ - Approve an event
# GET /api/events/{id}/attendance/ - Get event attendance
# POST /api/events/{id}/update_status/ - Update event status
# GET /api/event-attendance/by_student/?student_id=X - Get student attendance
# GET /api/event-attendance/by_event/?event_id=X - Get event attendance
from django.urls import path
from .views import (OrganizationCreateView, OrganizationListView, OrganizationDetailView, 
                    MembershipApplicationCreateView, StudentApplicationStatusView,
                    OrganizationApplicantsView, ApplicationActionView, OrganizationMembersView, 
                    KickMemberView, StudentJoinedOrganizationsView, ArchiveOrganizationView,
                    ToggleOrganizationActiveView)
from .position_views import PositionsListView, MemberPositionUpdateView
from .current_user_view import CurrentUserView
from .log_views import LogListView, LogDetailView
from .adviser_views import FacultyListView, OrganizationAdvisersView, UpdateOrganizationAdviserView, FacultyAdvisedOrganizationsView

urlpatterns = [

    path('api/', include(router.urls)),

    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:org_id>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('create/', OrganizationCreateView.as_view(), name='organization-create'),
    path('apply/', MembershipApplicationCreateView.as_view(), name='membership-application-create'),
    path('applications/<int:user_id>/', StudentApplicationStatusView.as_view(), name='student-application-status'),
    path('students/<int:student_id>/joined/', StudentJoinedOrganizationsView.as_view(), name='student-joined-organizations'),
    path('<int:org_id>/applicants/', OrganizationApplicantsView.as_view(), name='organization-applicants'),
    path('<int:org_id>/members/', OrganizationMembersView.as_view(), name='organization-members'),
    path('<int:org_id>/archive/', ArchiveOrganizationView.as_view(), name='organization-archive'),
    path('<int:org_id>/toggle-active/', ToggleOrganizationActiveView.as_view(), name='organization-toggle-active'),
    path('applications/<int:application_id>/action/', ApplicationActionView.as_view(), name='application-action'),
    path('positions/', PositionsListView.as_view(), name='positions-list'),
    path('members/<int:member_id>/position/', MemberPositionUpdateView.as_view(), name='member-position-update'),
    path('members/<int:member_id>/kick/', KickMemberView.as_view(), name='kick-member'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
    # Log endpoints
    path('logs/', LogListView.as_view(), name='log-list'),
    path('logs/<str:target_type>/<int:target_id>/', LogDetailView.as_view(), name='log-detail'),
    # Faculty and Adviser endpoints
    path('faculty/', FacultyListView.as_view(), name='faculty-list'),
    path('faculty/advised/', FacultyAdvisedOrganizationsView.as_view(), name='faculty-advised-organizations'),
    path('<int:org_id>/advisers/', OrganizationAdvisersView.as_view(), name='organization-advisers'),
    path('<int:org_id>/advisers/<int:adviser_term_id>/', UpdateOrganizationAdviserView.as_view(), name='update-adviser'),
    path('debug/memberships/', lambda request: __import__('rest_framework.response', fromlist=['Response']).Response({
        'memberships': list(__import__('apps.Organizations.models', fromlist=['OrganizationMembers']).OrganizationMembers.objects.all().values('id', 'user_id', 'organization_id__name', 'status'))
    }), name='debug-memberships'),
]

