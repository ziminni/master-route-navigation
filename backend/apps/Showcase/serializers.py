from __future__ import annotations

from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Media,
    ProjectTag,
    Project,
    ProjectMember,
    ProjectMedia,
    Competition,
    CompetitionMedia,
    CompetitionAchievement,
    CompetitionAchievementProject,
    CompetitionAchievementUser,
)
from . import services

User = get_user_model()


# ---------- basic model serializers ----------


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = "__all__"


class ProjectTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTag
        fields = ["id", "name"]


class ProjectMemberSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = ProjectMember
        fields = [
            "id",
            "project",
            "user",
            "role",
            "contributions",
            "username",
            "email",
        ]
        read_only_fields = ["id", "username", "email"]


class ProjectMediaSerializer(serializers.ModelSerializer):
    media = MediaSerializer(read_only=True)

    class Meta:
        model = ProjectMedia
        fields = ["id", "project", "media", "sort_order", "is_primary", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "title",
            "description",
            "submitted_by",
            "course_id",
            "organization_id",
            "status",
            "is_public",
            "publish_at",
            "created_at",
            "updated_at",
            "category",
            "context",
            "external_url",
            "author_display",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ProjectDetailSerializer(ProjectSerializer):
    tags = ProjectTagSerializer(many=True, read_only=True)
    media = MediaSerializer(many=True, read_only=True)
    members = ProjectMemberSerializer(source="memberships", many=True, read_only=True)
    posted_ago = serializers.SerializerMethodField()

    class Meta(ProjectSerializer.Meta):
        fields = ProjectSerializer.Meta.fields + [
            "tags",
            "media",
            "members",
            "posted_ago",
        ]

    def get_posted_ago(self, obj: Project) -> str:
        dt = obj.publish_at or obj.created_at
        return services._rel_time(dt)  # defined in services.py


class CompetitionMediaSerializer(serializers.ModelSerializer):
    media = MediaSerializer(read_only=True)

    class Meta:
        model = CompetitionMedia
        fields = ["id", "competition", "media", "sort_order", "is_primary", "created_at"]
        read_only_fields = ["id", "created_at"]


class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = [
            "id",
            "name",
            "organizer",
            "start_date",
            "end_date",
            "related_event_id",
            "description",
            "event_type",
            "external_url",
            "submitted_by",
            "status",
            "is_public",
            "publish_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CompetitionAchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetitionAchievement
        fields = [
            "id",
            "competition",
            "achievement_title",
            "result_recognition",
            "specific_awards",
            "notes",
            "awarded_at",
        ]
        read_only_fields = ["id"]


class CompetitionDetailSerializer(CompetitionSerializer):
    media = MediaSerializer(many=True, read_only=True)
    achievements = CompetitionAchievementSerializer(many=True, read_only=True)
    posted_ago = serializers.SerializerMethodField()

    class Meta(CompetitionSerializer.Meta):
        fields = CompetitionSerializer.Meta.fields + [
            "media",
            "achievements",
            "posted_ago",
        ]

    def get_posted_ago(self, obj: Competition) -> str:
        dt = obj.publish_at or obj.created_at
        return services._rel_time(dt)


class CompetitionAchievementProjectSerializer(serializers.ModelSerializer):
    project_title = serializers.CharField(source="project.title", read_only=True)

    class Meta:
        model = CompetitionAchievementProject
        fields = ["id", "achievement", "project", "project_title"]
        read_only_fields = ["id", "project_title"]


class CompetitionAchievementUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CompetitionAchievementUser
        fields = ["id", "achievement", "user", "role", "username", "email"]
        read_only_fields = ["id", "username", "email"]


# ---------- non-model serializer for card feed ----------


class ShowcaseCardSerializer(serializers.Serializer):
    """
    Matches the dicts returned by services.list_showcase_cards().
    """

    id = serializers.IntegerField()
    title = serializers.CharField()
    blurb = serializers.CharField(allow_blank=True)
    long_text = serializers.CharField(allow_blank=True)
    image = serializers.CharField(allow_null=True, required=False)
    images = serializers.ListField(child=serializers.CharField(), required=False)
    posted_ago = serializers.CharField(allow_blank=True)
    status = serializers.CharField(allow_null=True, required=False)
    author_display = serializers.CharField(
        allow_null=True, required=False, allow_blank=True
    )
    category = serializers.CharField(
        allow_null=True, required=False, allow_blank=True
    )
    context = serializers.CharField(
        allow_null=True, required=False, allow_blank=True
    )
    images_count = serializers.IntegerField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    external_url = serializers.CharField(
        allow_null=True, required=False, allow_blank=True
    )


# apps/Showcase/serializers.py
from rest_framework import serializers
from .models import Project, Competition


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class CompetitionSerializer(serializers.ModelSerializer):
    # publish_at needs to accept the format you send from PyQt: "YYYY-MM-DD HH:MM"
    publish_at = serializers.DateTimeField(
        required=False,
        allow_null=True,
        input_formats=["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "iso-8601"],
    )

    class Meta:
        model = Competition
        fields = "__all__"
