import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class DataManager:
    """
    DataManager for CISC Virtual Hub Messaging System.
    Handles all CRUD operations on a JSON database, with optional
    session info (username, roles, primary role, token).
    """

    def __init__(
        self,
        data_file_path = None,
        username: str = None,
        roles: list = None,
        primary_role: str = None,
        token: str = None
    ):
        if data_file_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_file_path = os.path.join(script_dir, "dummy_data.json")
        self.data_file_path = data_file_path
    
        self.data = self._load_data() 

        # Session info
        self.username = username
        self.roles = roles if roles else []
        self.primary_role = primary_role
        self.token = token

        self.current_user = username

    # ---------------------------
    # Load/Save Methods
    # ---------------------------
    def _load_data(self) -> Dict[str, Any]:
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Data file {self.data_file_path} not found. Creating empty database.")
        except json.JSONDecodeError:
            print(f"Data file {self.data_file_path} is corrupted. Creating empty database.")

        # Default empty database structure
        return {
            "users": [],
            "messages": [],
            "inquiries": [],
            "notifications": [],
            "conversations": [],
            "departments": [],
            "message_categories": [],
            "priority_levels": [],
            "message_statuses": []
        }

    def _save_data(self) -> bool:
        try:
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    # ---------------------------
    # User Management
    # ---------------------------
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        max_id = max([u.get('id', 0) for u in self.data['users']], default=0)
        user_data['id'] = max_id + 1
        user_data['created_at'] = datetime.now().isoformat()
        self.data['users'].append(user_data)
        return user_data if self._save_data() else None

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return next((u for u in self.data['users'] if u.get('id') == user_id), None)

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return next((u for u in self.data['users'] if u.get('email') == email), None)

    def get_all_users(self) -> List[Dict[str, Any]]:
        return self.data['users'].copy()

    def update_user(self, user_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, user in enumerate(self.data['users']):
            if user.get('id') == user_id:
                self.data['users'][i].update(updated_data)
                self.data['users'][i]['updated_at'] = datetime.now().isoformat()
                return self.data['users'][i] if self._save_data() else None
        return None

    def delete_user(self, user_id: int) -> bool:
        for i, user in enumerate(self.data['users']):
            if user.get('id') == user_id:
                del self.data['users'][i]
                return self._save_data()
        return False

    # ---------------------------
    # Message Management
    # ---------------------------
    def create_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        max_id = max([m.get('id', 0) for m in self.data['messages']], default=0)
        message_data['id'] = max_id + 1
        message_data['created_at'] = datetime.now().isoformat()
        message_data['updated_at'] = datetime.now().isoformat()
        self.data['messages'].append(message_data)
        return message_data if self._save_data() else None

    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        return next((m for m in self.data['messages'] if m.get('id') == message_id), None)

    def get_messages_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        return [m for m in self.data['messages'] if m.get('sender_id') == user_id or m.get('receiver_id') == user_id]

    def update_message(self, message_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, m in enumerate(self.data['messages']):
            if m.get('id') == message_id:
                self.data['messages'][i].update(updated_data)
                self.data['messages'][i]['updated_at'] = datetime.now().isoformat()
                return self.data['messages'][i] if self._save_data() else None
        return None

    def delete_message(self, message_id: int) -> bool:
        for i, m in enumerate(self.data['messages']):
            if m.get('id') == message_id:
                del self.data['messages'][i]
                return self._save_data()
        return False

    ## ---------------------------
# Inquiry Management
# ---------------------------
    def create_inquiry(self, inquiry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Creates a new inquiry and ensures it is linked to the correct conversation.
        If a conversation between the student and the recipient (admin/staff/faculty)
        already exists, reuse it. Otherwise, create a new one.
        """
        try:
            # === Step 1: Assign ID and timestamps ===
            max_id = max([i.get('id', 0) for i in self.data.get('inquiries', [])], default=0)
            inquiry_data['id'] = max_id + 1
            inquiry_data['created_at'] = datetime.now().isoformat()
            inquiry_data['updated_at'] = datetime.now().isoformat()

            self.data.setdefault('inquiries', []).append(inquiry_data)

            # === Step 2: Identify student and recipient ===
            student_id = inquiry_data.get('student_id')
            recipient_id = (
                inquiry_data.get('faculty_id') or
                inquiry_data.get('staff_id') or
                inquiry_data.get('admin_id')
            )

            if not student_id or not recipient_id:
                print("⚠️ Missing student or recipient ID.")
                return None

            subject = inquiry_data.get('subject', f"Inquiry #{inquiry_data['id']}")

            # === Step 3: Check if conversation already exists ===
            existing_convo = next(
                (c for c in self.data.get('conversations', [])
                if set(c.get('participants', [])) == {student_id, recipient_id}),
                None
            )

            if existing_convo:
                conversation_data = existing_convo
                print(f"ℹ️ Reusing existing conversation: {conversation_data['title']}")
            else:
                # === Step 4: Create a new conversation ===
                new_conv_id = max([c.get('id', 0) for c in self.data.get('conversations', [])], default=0) + 1
                conversation_data = {
                    "id": new_conv_id,
                    "participants": [student_id, recipient_id],
                    "title": subject,
                    "created_at": inquiry_data['created_at'],
                    "updated_at": inquiry_data['updated_at']
                }
                self.data.setdefault('conversations', []).append(conversation_data)
                print(f"✅ Created new conversation for inquiry: {subject}")

            # === Step 5: Link inquiry to this conversation ===
            inquiry_data['conversation_id'] = conversation_data['id']

            # === Step 6: Add the inquiry as a message ===
            message_entry = {
                "conversation_id": conversation_data['id'],
                "sender_id": student_id,
                "content": f"[New Inquiry] {subject}: {inquiry_data.get('description', '')}",
                "timestamp": inquiry_data['created_at'],
                "status": "unread"
            }
            self.data.setdefault('messages', []).append(message_entry)

            # === Step 7: Save changes ===
            self._save_data()
            print(f"💬 Inquiry linked to conversation ID {conversation_data['id']}")

            return inquiry_data

        except Exception as e:
            print(f"⚠️ Failed to create or link inquiry: {e}")
            return None


    def get_inquiry(self, inquiry_id: int) -> Optional[Dict[str, Any]]:
        return next((i for i in self.data['inquiries'] if i.get('id') == inquiry_id), None)

    def update_inquiry(self, inquiry_id: int, updated_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for i, inq in enumerate(self.data['inquiries']):
            if inq.get('id') == inquiry_id:
                self.data['inquiries'][i].update(updated_data)
                self.data['inquiries'][i]['updated_at'] = datetime.now().isoformat()
                return self.data['inquiries'][i] if self._save_data() else None
        return None

    def delete_inquiry(self, inquiry_id: int) -> bool:
        for i, inq in enumerate(self.data['inquiries']):
            if inq.get('id') == inquiry_id:
                del self.data['inquiries'][i]
                return self._save_data()
        return False

    # ---------------------------
    # Conversation Management
    # ---------------------------
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        max_id = max([c.get('id', 0) for c in self.data['conversations']], default=0)
        conversation_data['id'] = max_id + 1
        conversation_data['created_at'] = datetime.now().isoformat()
        conversation_data['updated_at'] = datetime.now().isoformat()
        self.data['conversations'].append(conversation_data)
        return conversation_data if self._save_data() else None

    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        return next((c for c in self.data['conversations'] if c.get('id') == conversation_id), None)

    def get_conversations_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        return [c for c in self.data['conversations'] if user_id in c.get('participants', [])]

    # ---------------------------
    # Notification Management
    # ---------------------------
    def create_notification(self, notification_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        max_id = max([n.get('id', 0) for n in self.data['notifications']], default=0)
        notification_data['id'] = max_id + 1
        notification_data['created_at'] = datetime.now().isoformat()
        self.data['notifications'].append(notification_data)
        return notification_data if self._save_data() else None

    def get_notifications_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        return [n for n in self.data['notifications'] if n.get('user_id') == user_id]

    def mark_notification_as_read(self, notification_id: int) -> bool:
        for i, n in enumerate(self.data['notifications']):
            if n.get('id') == notification_id:
                self.data['notifications'][i]['is_read'] = True
                return self._save_data()
        return False

    # ---------------------------
    # Utility Methods
    # ---------------------------
    def reload_data(self) -> dict:
        self.data = self._load_data()
        return self.data

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        if self.username:
            return next((u for u in self.data['users'] if u.get('name') == self.username), None)
        return None

     # ---------------------------
    # Inquiry query helpers
    # ---------------------------
    def get_inquiries_by_faculty(self, faculty_id: int) -> List[Dict[str, Any]]:
        """Return inquiries assigned to a faculty member (most recent first)."""
        self.reload_data()  # ✅ ensures latest data from file
        inqs = [i for i in self.data.get('inquiries', []) if i.get('faculty_id') == faculty_id]
        inqs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return inqs


    def get_inquiries_by_staff(self, staff_id: int) -> List[Dict[str, Any]]:
        """Return inquiries assigned to a staff member (most recent first)."""
        inqs = [i for i in self.data.get('inquiries', []) if i.get('staff_id') == staff_id]
        inqs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return inqs

    def get_inquiries_by_admin(self, admin_id: int) -> List[Dict[str, Any]]:
        """Return inquiries assigned to an admin (most recent first)."""
        inqs = [i for i in self.data.get('inquiries', []) if i.get('admin_id') == admin_id]
        inqs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return inqs

    def get_inquiries_by_recipient(self, recipient_id: int) -> List[Dict[str, Any]]:
        """
        Generic: return inquiries where recipient_id matches any recipient field.
        Useful when the caller doesn't care about role (faculty/staff/admin).
        """
        inqs = [
            i for i in self.data.get('inquiries', [])
            if recipient_id in (i.get('faculty_id'), i.get('staff_id'), i.get('admin_id'))
        ]
        inqs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return inqs