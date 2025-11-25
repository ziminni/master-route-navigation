from rest_framework import serializers
from .models import FacultyFeedbackMessage


class FacultyFeedbackMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source="sender.username", read_only=True)
    receiver_name = serializers.CharField(source="receiver.username", read_only=True)

    class Meta:
        model = FacultyFeedbackMessage
        fields = [
            "id", "sender", "sender_name",
            "receiver", "receiver_name",
            "subject", "message",
            "linked_final_grade",
            "is_read", "created_at"
        ]
        read_only_fields = ["id", "sender", "created_at", "is_read"]