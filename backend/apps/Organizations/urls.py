from django.urls import path
from .views import OrganizationCreateView, OrganizationListView, OrganizationDetailView

urlpatterns = [
    path('', OrganizationListView.as_view(), name='organization-list'),
    path('<int:org_id>/', OrganizationDetailView.as_view(), name='organization-detail'),
    path('create/', OrganizationCreateView.as_view(), name='organization-create'),
]
