from rest_framework import serializers
from . import models
from django.conf import settings


class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.House
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "banner",
            "logo",
            "members_count",
            "points_total",
            "behavioral_points",
            "competitive_points",
            "created_at",
            "updated_at",
        ]


class HouseMembershipSerializer(serializers.ModelSerializer):
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = models.HouseMembership
        fields = ["id", "user", "user_display", "house", "role", "year_level", "avatar", "points", "is_active", "joined_at", "created_at"]

    def get_user_display(self, obj):
        try:
            return str(obj.user)
        except Exception:
            return None


class HouseEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.HouseEvent
        fields = ["id", "house", "title", "description", "start_date", "end_date", "img", "is_competition", "created_by", "created_at"]


class EventParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.EventParticipant
        fields = ["id", "event", "user", "role", "confirmed", "created_at"]


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Announcement
        fields = ["id", "house", "title", "content", "author", "pinned", "created_at"]
