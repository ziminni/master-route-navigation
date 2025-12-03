from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import (
    UserViewSet,
    MessageViewSet,
    ConversationViewSet,
    BroadcastListView,
)

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"messages", MessageViewSet, basename="message")
router.register(r"conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
    path("broadcasts/", BroadcastListView.as_view(), name="broadcast-list"),
]
