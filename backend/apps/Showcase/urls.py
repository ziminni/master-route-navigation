# apps/Showcase/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ShowcaseCardsAPIView,
    ShowcaseCategoriesAPIView,
    ProjectMediaAPIView,
    CompetitionMediaAPIView,
    # your existing viewsets below...
)

router = DefaultRouter()
# existing router registrations, e.g.:
# router.register("media", MediaViewSet, basename="showcase-media")
# router.register("projects", ProjectViewSet, basename="showcase-project")
# router.register("competitions", CompetitionViewSet, basename="showcase-competition")
# router.register("achievements", AchievementViewSet, basename="showcase-achievement")

urlpatterns = [
    path("cards/",      ShowcaseCardsAPIView.as_view(),      name="showcase-cards"),
    path("categories/", ShowcaseCategoriesAPIView.as_view(), name="showcase-categories"),

    # *** new endpoints expected by ShowcaseDBHelper ***
    path("projects/<int:pk>/media/",     ProjectMediaAPIView.as_view(),
         name="showcase-project-media"),
    path("competitions/<int:pk>/media/", CompetitionMediaAPIView.as_view(),
         name="showcase-competition-media"),

    # router-based endpoints: /media/, /projects/, /projects/<pk>/, etc.
    path("", include(router.urls)),
]
