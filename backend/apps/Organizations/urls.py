from django.urls import path
from .views import (OrganizationCreateView, OrganizationListView, OrganizationDetailView, 
                    MembershipApplicationCreateView, StudentApplicationStatusView,
                    OrganizationApplicantsView, ApplicationActionView, OrganizationMembersView)
from .position_views import PositionsListView, MemberPositionUpdateView
from .current_user_view import CurrentUserView

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:org_id>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('create/', OrganizationCreateView.as_view(), name='organization-create'),
    path('apply/', MembershipApplicationCreateView.as_view(), name='membership-application-create'),
    path('applications/<int:user_id>/', StudentApplicationStatusView.as_view(), name='student-application-status'),
    path('<int:org_id>/applicants/', OrganizationApplicantsView.as_view(), name='organization-applicants'),
    path('<int:org_id>/members/', OrganizationMembersView.as_view(), name='organization-members'),
    path('applications/<int:application_id>/action/', ApplicationActionView.as_view(), name='application-action'),
    path('positions/', PositionsListView.as_view(), name='positions-list'),
    path('members/<int:member_id>/position/', MemberPositionUpdateView.as_view(), name='member-position-update'),
    path('current-user/', CurrentUserView.as_view(), name='current-user'),
]
