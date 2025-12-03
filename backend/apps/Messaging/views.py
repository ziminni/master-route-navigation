from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import Conversation, Message
from .serializers import UserSerializer, ConversationSerializer, MessageSerializer
from rest_framework import generics
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import viewsets, permissions
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser

from .models import Message
from .serializers import MessageSerializer


User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        username = self.request.query_params.get("username")
        if username:
            qs = qs.filter(username__iexact=username)

        email = self.request.query_params.get("email")
        if email:
            qs = qs.filter(email__iexact=email)

        return qs




class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        qs = (
            Message.objects
            .filter(conversation__participants=user)
            .select_related("sender", "receiver", "conversation")
        )
        conv_id = self.request.query_params.get("conversation")
        if conv_id:
            qs = qs.filter(conversation_id=conv_id)

        receiver = self.request.query_params.get("receiver")
        if receiver:
            qs = qs.filter(receiver_id=receiver)

        msg_type = self.request.query_params.get("message_type")
        if msg_type:
            qs = qs.filter(message_type=msg_type)

        return qs

    def perform_create(self, serializer):
        """
        Create a new message and:
        - If it's a broadcast, send to 'system_broadcasts' group.
        - Also send all messages to a per-user or per-conversation group
          so frontends can receive regular chat updates in real time.
        """
        print("[DRF] MessageViewSet.perform_create by", self.request.user, "data:", self.request.data)

        message = serializer.save(sender=self.request.user)
        channel_layer = get_channel_layer()
        if channel_layer is None:
            return  # no channel layer configured; skip WS notify


        base_payload = {
            "id": message.id,
            "subject": getattr(message, "subject", None),
            "content": message.content,
            "sender_id": message.sender_id,
            "receiver_id": getattr(message, "receiver_id", None),
            "conversation_id": getattr(message, "conversation_id", None),
            "priority": getattr(message, "priority", None),
            "department": getattr(message, "department", None),
            "status": getattr(message, "status", None),
            "created_at": message.created_at.isoformat(),
            "sender_name": getattr(message, "sender_name", str(message.sender)),
        }

        # 1) Broadcast messages → global group (unchanged)
        if message.is_broadcast and message.message_type == "broadcast":
            async_to_sync(channel_layer.group_send)(
                "system_broadcasts",
                {
                    "type": "broadcast_message",
                    "data": base_payload,
                },
            )

        # 2) Regular messages → per-user group (unchanged)
        if getattr(message, "receiver_id", None):
            user_group = f"user_{message.receiver_id}"
            async_to_sync(channel_layer.group_send)(
                user_group,
                {
                    "type": "chat_message",
                    "data": base_payload,
                },
            )

        # 3) Regular messages → per-conversation group (unchanged)
        if getattr(message, "conversation_id", None):
            conv_group = f"conversation_{message.conversation_id}"
            async_to_sync(channel_layer.group_send)(
                conv_group,
                {
                    "type": "chat_message",
                    "data": base_payload,
                },
            )

        # 4) NEW: also send chat events to the global broadcasts group
        async_to_sync(channel_layer.group_send)(
            "system_broadcasts",
            {
                "type": "chat_message",  # handled by BroadcastConsumer.chat_message
                "data": base_payload,
            },
        )




class BroadcastListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(
            is_broadcast=True,
            message_type="broadcast",
        ).order_by("-created_at")
    def perform_create(self, serializer):
        user = self.request.user
        print("[DRF] MessageViewSet.perform_create by", user, "data:", self.request.data)
        serializer.save(sender=user)


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Conversation.objects.all()
        participant_id = self.request.query_params.get("participant")
        if participant_id:
            qs = qs.filter(participants__id=participant_id)
        return qs

    def perform_create(self, serializer):
        conv = serializer.save(creator=self.request.user)
        conv.participants.add(self.request.user)
