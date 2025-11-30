from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'houses', views.HouseViewSet, basename='house')
router.register(r'memberships', views.HouseMembershipViewSet, basename='housemembership')
router.register(r'events', views.HouseEventViewSet, basename='houseevent')
router.register(r'participants', views.EventParticipantViewSet, basename='eventparticipant')
router.register(r'announcements', views.AnnouncementViewSet, basename='announcement')

urlpatterns = [
    path("api/house/", include(router.urls)),
]
