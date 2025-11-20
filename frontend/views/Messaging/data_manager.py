from django.contrib.auth.models import User
from backend.apps.Messaging.models import MessageThread, ThreadParticipant, Message
from datetime import datetime
from typing import List, Dict, Any, Optional

class DataManager:
    """
    DataManager for CISC Virtual Hub Messaging System.
    Handles all CRUD operations on the Django database with optional
    session info (username, roles, primary role, token).
    """

    def __init__(
        self,
        username: str = None,
        roles: list = None,
        primary_role: str = None,
        token: str = None
    ):
        # Session info
        self.username = username
        self.roles = roles if roles else []
        self.primary_role = primary_role
        self.token = token
        self.current_user = username

    # ---------------------------
    # User Management
    # ---------------------------
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Uses Django's built-in User model
        new_user = User.objects.create_user(
            username=user_data.get('username'),
            email=user_data.get('email'),
            password=user_data.get('password')
        )
        new_user.first_name = user_data.get('first_name', '')
        new_user.last_name = user_data.get('last_name', '')
        new_user.save()
        return {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'created_at': str(new_user.date_joined)
        }

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            user = User.objects.get(pk=user_id)
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        except User.DoesNotExist:
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        user = User.objects.filter(email=email).first()
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        return None

    def get_all_users(self) -> List[Dict[str, Any]]:
        return [
            {
                'id': u.id,
                'username': u.username,
                'email': u.email
            }
            for u in User.objects.all()
        ]

    def update_user(self, user_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            user = User.objects.get(pk=user_id)
            for key, value in updated_data.items():
                setattr(user, key, value)
            user.save()
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        except User.DoesNotExist:
            return None

    def delete_user(self, user_id: int) -> bool:
        try:
            user = User.objects.get(pk=user_id)
            user.delete()
            return True
        except User.DoesNotExist:
            return False

    # ---------------------------
    # Message Management
    # ---------------------------
    def create_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        # Finds the thread and sender, creates new message
        try:
            thread = MessageThread.objects.get(pk=message_data['thread_id'])
            sender = User.objects.get(pk=message_data['sender_id'])
            msg = Message.objects.create(
                thread=thread,
                sender=sender,
                content=message_data['content']
            )
            return {
                'id': msg.id,
                'thread_id': msg.thread.id,
                'sender_id': msg.sender.id,
                'content': msg.content,
                'created_at': str(msg.sent_at)
            }
        except Exception as e:
            print(f"Error creating message: {e}")
            return None

    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        msg = Message.objects.filter(pk=message_id).first()
        if msg:
            return {
                'id': msg.id,
                'thread_id': msg.thread.id,
                'sender_id': msg.sender.id,
                'content': msg.content,
                'created_at': str(msg.sent_at)
            }
        return None

    def get_messages_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        return [
            {
                'id': m.id,
                'thread_id': m.thread.id,
                'sender_id': m.sender.id,
                'content': m.content,
                'created_at': str(m.sent_at)
            }
            for m in Message.objects.filter(sender__id=user_id)
        ]

    def update_message(self, message_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg = Message.objects.filter(pk=message_id).first()
        if msg:
            for key, value in updated_data.items():
                setattr(msg, key, value)
            msg.save()
            return {
                'id': msg.id,
                'thread_id': msg.thread.id,
                'sender_id': msg.sender.id,
                'content': msg.content,
                'created_at': str(msg.sent_at)
            }
        return None

    def delete_message(self, message_id: int) -> bool:
        msg = Message.objects.filter(pk=message_id).first()
        if msg:
            msg.delete()
            return True
        return False

    # ---------------------------
    # Conversation & Thread Management
    # ---------------------------
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            thread = MessageThread.objects.create(
                subject=conversation_data.get('subject', '')
            )
            participants = conversation_data.get('participants', [])
            for user_id in participants:
                user = User.objects.get(pk=user_id)
                ThreadParticipant.objects.create(thread=thread, user=user)
            return {
                'id': thread.id,
                'subject': thread.subject,
                'created_at': str(thread.created_at)
            }
        except Exception as e:
            print(f"Error creating conversation or thread: {e}")
            return None

    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        thread = MessageThread.objects.filter(pk=conversation_id).first()
        if thread:
            return {
                'id': thread.id,
                'subject': thread.subject,
                'participants': [p.user.id for p in thread.participants.all()],
                'created_at': str(thread.created_at)
            }
        return None

    def get_conversations_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        return [
            {
                'id': thread.id,
                'subject': thread.subject,
                'created_at': str(thread.created_at)
            }
            for thread in MessageThread.objects.filter(participants__user__id=user_id).distinct()
        ]

    # ---------------------------
    # Notification Management
    # ---------------------------
    # For notification logic, recommend making a Django model for Notification
    # Example:
    # class Notification(models.Model):
    #     user = models.ForeignKey(User, on_delete=models.CASCADE)
    #     content = models.TextField()
    #     is_read = models.BooleanField(default=False)
    #     created_at = models.DateTimeField(auto_now_add=True)

    # Then adapt corresponding CRUD logic similar to above.

    # ---------------------------
    # Utility Methods
    # ---------------------------
    # Reload and session helper logic can be updated similarly if needed,
    # but session management would be handled by Django's authentication framework.

    # Inquiry helpers would create or query threads/messages/participants similarly.

    # Use Django ORM filters for all list, get, and update operations.

