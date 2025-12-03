# apps/Showcase/api_views.py
from rest_framework import viewsets, permissions
from .models import Project, Competition
from .serializers import ProjectSerializer, CompetitionSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related("submitted_by")
    serializer_class = ProjectSerializer
    # while debugging, keep this open; later tighten permissions
    permission_classes = [permissions.AllowAny]


class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all().select_related("submitted_by")
    serializer_class = CompetitionSerializer
    permission_classes = [permissions.AllowAny]
