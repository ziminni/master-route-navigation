# apps/Showcase/api_urls.py
from rest_framework.routers import DefaultRouter
from .api_views import ProjectViewSet, CompetitionViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="showcase-project")
router.register(r"competitions", CompetitionViewSet, basename="showcase-competition")

urlpatterns = router.urls