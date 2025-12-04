from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

app_name = 'documents'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'document-types', DocumentTypeViewSet, basename='documenttype')
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'approvals', DocumentApprovalViewSet, basename='approval')
router.register(r'activities', ActivityLogViewSet, basename='activity')

urlpatterns = [
    path('', include(router.urls)),
]