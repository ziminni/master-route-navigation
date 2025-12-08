from rest_framework import serializers

from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = (
            "id",
            "submission_type",
            "subject",
            "message",
            "is_anonymous",
            "resolved",
            "admin_response",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "resolved", "admin_response", "created_at", "updated_at")

    def create(self, validated_data):
        request = self.context.get("request")
        user = None
        if request is not None and getattr(request, "user", None) and request.user.is_authenticated:
            user = request.user

        # If the client explicitly sets is_anonymous, prefer that; otherwise
        # treat missing value as False.
        is_anon = validated_data.pop("is_anonymous", False)

        # If anonymous submission requested, do not attach user
        if is_anon:
            user = None

        feedback = Feedback.objects.create(user=user, is_anonymous=is_anon, **validated_data)
        return feedback
