from django.urls import path
from .views import OrganizationCreateView, OrganizationListView, OrganizationDetailView, MembershipApplicationCreateView, StudentApplicationStatusView

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:org_id>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('create/', OrganizationCreateView.as_view(), name='organization-create'),
    path('apply/', MembershipApplicationCreateView.as_view(), name='membership-application-create'),
    path('applications/<int:user_id>/', StudentApplicationStatusView.as_view(), name='student-application-status'),
]
