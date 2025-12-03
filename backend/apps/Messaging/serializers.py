from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Conversation, Message

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    # Map to the keys your DataManager expects in get_user_list_for_management
    name = serializers.SerializerMethodField()
    role = serializers.CharField(source="role_type")
    department = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "name",
            "role",
            "department"
        ]

    def get_name(self, obj):
        return obj.get_full_name() or obj.username
    def get_department(self, obj):
    # Simple example: use faculty/ staff profile, or return
        if hasattr(obj, "faculty_profile") and obj.faculty_profile.faculty_department:
            return obj.faculty_profile.faculty_department.department_name
        if hasattr(obj, "staff_profile") and obj.staff_profile.faculty_department:
            return obj.staff_profile.faculty_department.department_name
        return ""

class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "creator",
            "type",
            "participants",
            "created_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "subject",
            "content",
            "priority",
            "status",
            "department",
            "message_type",
            "is_broadcast",
            "sender",
            "receiver",
            "sender_name",
            "attachment",
            "created_at",
            "updated_at",
        ]
        # sender must not be provided by client
        read_only_fields = ["sender", "sender_name", "created_at", "updated_at"]

    def validate_content(self, value):

        if not value or not value.strip():

            raise serializers.ValidationError("Content cannot be empty.")

        return value

    def create(self, validated_data):
        """
        Always set sender from the authenticated user (request.user).
        """
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            raise serializers.ValidationError(
                {"detail": "Authenticated user required to send messages."}
            )

        validated_data["sender"] = user
        return super().create(validated_data)
