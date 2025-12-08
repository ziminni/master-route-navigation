from __future__ import annotations

from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from .models import Project, Competition, Media
from .serializers import MediaSerializer

from .models import (
    Media,
    Project,
    ProjectMember,
    Competition,
    CompetitionAchievement,
)
from .serializers import (
    MediaSerializer,
    ProjectSerializer,
    ProjectDetailSerializer,
    ProjectMemberSerializer,
    CompetitionSerializer,
    CompetitionDetailSerializer,
    CompetitionAchievementSerializer,
    ShowcaseCardSerializer,
)
from . import services


# ---------- viewsets ----------


class MediaViewSet(viewsets.ModelViewSet):
    """
    Basic CRUD for Media. File handling can be layered on later.
    """

    queryset = Media.objects.all().order_by("-created_at")
    serializer_class = MediaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProjectViewSet(viewsets.ModelViewSet):
    """
    CRUD for projects. Supports simple filter query params:

        GET /projects/?status=pending&category=capstone&is_public=1&q=smart
    """

    queryset = Project.objects.all().order_by("-created_at")
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ProjectDetailSerializer
        return ProjectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        status_param = params.get("status")
        category = params.get("category")
        is_public = params.get("is_public")
        q = params.get("q")

        if status_param:
            qs = qs.filter(status=status_param)
        if category:
            qs = qs.filter(category=category)
        if is_public is not None:
            val = (is_public or "").lower()
            if val in ("1", "true", "yes"):
                qs = qs.filter(is_public=True)
            elif val in ("0", "false", "no"):
                qs = qs.filter(is_public=False)
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(author_display__icontains=q)
            )
        return qs

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.AllowAny],
        url_path="set-tags",
    )
    def set_tags(self, request, pk=None) -> Response:
        """
        Replace the project's tags with request.data["tags"] (list of names).
        Mirrors old set_project_tags().
        """
        tags = request.data.get("tags", [])
        if not isinstance(tags, list):
            return Response(
                {"detail": "tags must be a list of strings."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tags_clean = [str(t).strip() for t in tags if str(t).strip()]
        services.set_project_tags(int(pk), tags_clean)
        return Response({"status": "ok", "tags": tags_clean})

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="add-member",
    )
    def add_member(self, request, pk=None) -> Response:
        """
        Add a member to the project. Expects user_id, role, contributions.
        Mirrors add_member().
        """
        user_id = request.data.get("user_id")
        role = request.data.get("role")
        contributions = request.data.get("contributions")

        if not user_id:
            return Response(
                {"detail": "user_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        member_id = services.add_member(
            int(pk),
            int(user_id),
            role,
            contributions,
        )
        member = ProjectMember.objects.get(pk=member_id)
        data = ProjectMemberSerializer(member).data
        return Response(data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="remove-member",
    )
    def remove_member(self, request, pk=None) -> Response:
        """
        Remove a member by project_members_id (in body).
        """
        pm_id = request.data.get("project_members_id")
        if not pm_id:
            return Response(
                {"detail": "project_members_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        services.remove_member(int(pm_id))
        return Response(status=status.HTTP_204_NO_CONTENT)


class CompetitionViewSet(viewsets.ModelViewSet):
    """
    CRUD for competitions. q/status filters match list_competitions().
    """

    queryset = Competition.objects.all().order_by("-created_at")
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CompetitionDetailSerializer
        return CompetitionSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params

        status_param = params.get("status")
        q = params.get("q")

        if status_param:
            qs = qs.filter(status=status_param)
        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(organizer__icontains=q)
                | Q(description__icontains=q)
            )
        return qs

    @action(
        detail=True,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        url_path="with-relations",
    )
    def with_relations(self, request, pk=None) -> Response:
        """
        Rich read-only view: competition + achievements + related
        projects/users. Mirrors get_competition_with_relations().
        """
        data = services.get_competition_with_relations(int(pk))
        if not data:
            return Response(
                {"detail": "Not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(data)


class CompetitionAchievementViewSet(viewsets.ModelViewSet):
    queryset = CompetitionAchievement.objects.all().order_by("-awarded_at", "-id")
    serializer_class = CompetitionAchievementSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# ---------- non-viewset API views ----------


class ShowcaseCardsAPIView(APIView):
    """
    Read-only feed used by the Showcase cards.

    Query params:
        kind=project|competition (default: project)
        q=...
        status=...
        limit=...  default 50
        offset=... default 0
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs) -> Response:
        kind = (request.query_params.get("kind") or "project").lower()
        if kind not in ("project", "competition"):
            return Response(
                {"detail": "kind must be 'project' or 'competition'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        q = request.query_params.get("q") or None
        status_param = request.query_params.get("status") or None

        try:
            limit = int(request.query_params.get("limit", 50))
        except ValueError:
            limit = 50
        try:
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            offset = 0

        cards = services.list_showcase_cards(
            kind=kind,
            q=q,
            status=status_param,
            limit=limit,
            offset=offset,
        )
        serializer = ShowcaseCardSerializer(cards, many=True)
        return Response(serializer.data)


class ShowcaseCategoriesAPIView(APIView):
    """
    Combined category list from projects.category + competitions.event_type.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, *args, **kwargs) -> Response:
        cats = services.list_showcase_categories()
        return Response(cats)



class ProjectMediaAPIView(APIView):
    """
    GET /api/showcase/projects/<pk>/media/
    Returns all media rows linked to a project.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        project = get_object_or_404(Project, pk=pk)

        # If Media has FK to Project:
        qs = Media.objects.filter(project=project)

        # If you used ManyToMany with related_name="media", then instead:
        # qs = project.media.all()

        ser = MediaSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)


class CompetitionMediaAPIView(APIView):
    """
    GET /api/showcase/competitions/<pk>/media/
    Returns all media rows linked to a competition.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        comp = get_object_or_404(Competition, pk=pk)

        # If Media has FK to Competition:
        qs = Media.objects.filter(competition=comp)

        # Or ManyToMany: qs = comp.media.all()

        ser = MediaSerializer(qs, many=True, context={"request": request})
        return Response(ser.data)
