import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class DataManager:
    """
    DataManager for CISC Virtual Hub Messaging System.

    Uses HTTP requests to talk to the Django backend API instead of direct ORM.
    Holds session info (username, roles, token) and exposes helpers for
    users, messages, conversations, and admin-style analytics.
    """

    def __init__(
            self,
            username: str | None = None,
            roles: list | None = None,
            primary_role: str | None = None,
            token: str | None = None,
            base_url: str = "http://127.0.0.1:8001/api",
    ):
        # Session info for the current logged-in user
        self.username = username
        self.roles = roles or []
        self.primary_role = primary_role
        self.token = token
        self.current_user = username
        self.base_url = base_url.rstrip("/")

        # In-memory caches for performance
        self._messages_cache: Optional[list[dict]] = None
        self._users_cache: Optional[list[dict]] = None
        self._inquiries_cache: Optional[list[dict]] = None

    # ---------------------------
    # Internal helpers
    # ---------------------------
    def _headers(self) -> Dict[str, str]:
        """
        Common HTTP headers for all API calls, including JWT Authorization
        when a token is available.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _handle_response(
            self, resp: requests.Response
    ) -> Optional[Dict[str, Any] | List[Dict[str, Any]]]:
        """
        Centralized HTTP response handling.

        - For 2xx responses, attempts to parse JSON and returns it.
        - For non-2xx, logs a short error snippet and returns None.
        """
        if 200 <= resp.status_code < 300:
            try:
                return resp.json()
            except ValueError:
                print("[DataManager] _handle_response: response has no JSON body")
                return None
        print(f"[DataManager] HTTP {resp.status_code}: {resp.text[:500]}")
        return None

    def clear_cache(self):
        """Clear all caches so next calls hit Django again."""
        self._messages_cache = None
        self._users_cache = None
        self._inquiries_cache = None

    def reload_data(self):
        """Public helper to invalidate caches."""
        self.clear_cache()

    # ---------------------------
    # User helpers
    # ---------------------------
    def get_all_users(self) -> list[dict]:
        url = f"{self.base_url}/users/"
        resp = requests.get(url, headers=self._headers(), timeout=10)
        data = self._handle_response(resp)
        if isinstance(data, list):
            self._users_cache = data
            return data
        return []

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/users/{user_id}/"
        resp = requests.get(url, headers=self._headers())
        return self._handle_response(resp)

    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """
        Resolve a user by username using the cached user list.
        Returns the matching user id or None.
        """
        users = self.get_all_users()
        username_lower = username.strip().lower()
        for u in users:
            if str(u.get("username", "")).lower() == username_lower:
                return u.get("id")
        return None



    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a user by email using /users/?email=<email>.
        Returns the first matching record or None.
        """
        url = f"{self.base_url}/users/"
        resp = requests.get(url, params={"email": email}, headers=self._headers())
        data = self._handle_response(resp)

        # API should return a list; treat anything else as "no match"
        if isinstance(data, list) and data:
            return data[0]

        # if list is empty or data is not a list, treat as no user
        return None


    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/users/"
        resp = requests.post(url, json=user_data, headers=self._headers())
        self._users_cache = None
        return self._handle_response(resp)

    def update_user(
            self, user_id: int, updated_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/users/{user_id}/"
        resp = requests.patch(url, json=updated_data, headers=self._headers())
        self._users_cache = None
        return self._handle_response(resp)

    def delete_user(self, user_id: int) -> bool:
        url = f"{self.base_url}/users/{user_id}/"
        resp = requests.delete(url, headers=self._headers())
        self._users_cache = None
        return resp.status_code == 204

    def get_username_by_id(self, user_id: int) -> Optional[str]:
        """Resolve username via cache or /users/<id>/."""
        if not user_id:
            return None

        if self._users_cache:
            for u in self._users_cache:
                if u.get("id") == user_id:
                    return u.get("username")

        url = f"{self.base_url}/users/{user_id}/"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
        except Exception as e:
            print(f"[DataManager] get_username_by_id error: {e}")
            return None

        data = self._handle_response(resp)
        if not isinstance(data, dict):
            return None
        return data.get("username")

    def get_current_user_id(self) -> Optional[int]:
        """
        Resolve the current user's numeric id from /users/ using
        self.username and (optionally) self.primary_role (mapped from groups).
        """
        if not self.username:
            print("[DataManager] get_current_user_id: no username set")
            return None

        users = self.get_all_users()
        target_role = (self.primary_role or "").lower()

        # First pass: username + role match
        for u in users:
            uname = str(u.get("username", ""))
            groups = u.get("groups", []) or []
            groups_list = [groups] if isinstance(groups, str) else [str(g) for g in groups]
            roles_lower = [g.lower() for g in groups_list]

            if uname == self.username:
                if target_role and target_role not in roles_lower:
                    continue
                return u.get("id")

        # Fallback: username only
        for u in users:
            if str(u.get("username", "")) == self.username:
                return u.get("id")

        print("[DataManager] get_current_user_id: no match for", self.username)
        return None


    def update_conversation_title(self, conv_id: int, title: str) -> Optional[dict]:
        url = f"{self.base_url}/conversations/{conv_id}/"
        resp = requests.patch(url, json={"title": title}, headers=self._headers())
        return self._handle_response(resp)


    # ---------------------------
    # Message Management
    # ---------------------------
    def create_message(self, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a message.

        The backend (DRF) sets `sender` from request.user, so the payload
        here intentionally does not include a `sender` field.
        """

        url = f"{self.base_url}/messages/"
        resp = requests.post(url, json=message_data, headers=self._headers())
        self._messages_cache = None
        return self._handle_response(resp)

    def create_message_with_attachment(
            self,
            message_data: Dict[str, Any],
            file_path: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a message with a file attachment (multipart/form-data).
        """
        url = f"{self.base_url}/messages/"
        payload = {**message_data}

        headers = self._headers()
        headers.pop("Content-Type", None)  # let requests set multipart boundary

        with open(file_path, "rb") as f:
            files = {"attachment": f}
            resp = requests.post(url, data=payload, files=files, headers=headers)

        self._messages_cache = None
        return self._handle_response(resp)

    def get_message(self, message_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/messages/{message_id}/"
        resp = requests.get(url, headers=self._headers())
        return self._handle_response(resp)

    def get_all_messages(self, force: bool = False) -> List[Dict[str, Any]]:
        """
        Get all messages visible to the current user.

        If force=True, bypass the in-memory cache and hit the API again.
        """
        if not force and self._messages_cache is not None:
            return self._messages_cache

        url = f"{self.base_url}/messages/"
        resp = requests.get(url, headers=self._headers())
        data = self._handle_response(resp)

        if isinstance(data, list):
            self._messages_cache = data
            return data
        if isinstance(data, dict) and "results" in data:
            results = data.get("results", [])
            self._messages_cache = results
            return results
        return []


    def get_messages_for_receiver(self, user_id: int) -> List[Dict[str, Any]]:
        """
        All messages where a specific user is the receiver.

        This is used for inbox-style views and intentionally does NOT
        filter by message_type so replies (message_type='message') are
        visible alongside inquiries.
        """
        url = f"{self.base_url}/messages/"
        resp = requests.get(
            url,
            params={"receiver": user_id},
            headers=self._headers(),
        )
        data = self._handle_response(resp)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data.get("results", [])
        return []

    def update_message(
            self, message_id: int, updated_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/messages/{message_id}/"
        resp = requests.patch(url, json=updated_data, headers=self._headers())
        self._messages_cache = None
        return self._handle_response(resp)

    def delete_message(self, message_id: int) -> bool:
        url = f"{self.base_url}/messages/{message_id}/"
        resp = requests.delete(url, headers=self._headers())
        self._messages_cache = None
        return resp.status_code == 204

    # Inquiry helpers (message_type = "inquiry")
    def get_inquiry_messages(self) -> list[dict]:
        """
        All inquiry-type messages visible to current user (from cache),
        filtered client-side by message_type='inquiry'.
        """
        return [
            m for m in self.get_all_messages()
            if m.get("message_type") == "inquiry"
        ]

    def get_inquiries_by_faculty(self, faculty_id: int) -> list[dict]:
        """
        Inquiries where this faculty is the receiver.

        Uses /messages/?receiver=<id>&message_type=inquiry so only inquiry-type
        messages are returned (useful for dedicated Inquiry screens).
        """
        url = f"{self.base_url}/messages/"
        params = {
            "receiver": faculty_id,
            "message_type": "inquiry",
        }
        try:
            resp = requests.get(
                url, params=params, headers=self._headers(), timeout=10
            )
        except Exception as e:
            print("[DataManager] get_inquiries_by_faculty error:", e)
            return []

        data = self._handle_response(resp)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data.get("results", [])
        return []

    def create_inquiry(self, inquiry_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create an inquiry stored as Message with message_type='inquiry'.
        """
        url = f"{self.base_url}/messages/"
        resp = requests.post(url, json=inquiry_data, headers=self._headers())
        self._messages_cache = None
        return self._handle_response(resp)

    # ---------------------------
    # Conversation Management
    # ---------------------------
    def create_conversation(self, conversation_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/conversations/"
        resp = requests.post(url, json=conversation_data, headers=self._headers())
        return self._handle_response(resp)

    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/conversations/{conversation_id}/"
        resp = requests.get(url, headers=self._headers())
        return self._handle_response(resp)

    def get_conversations_by_user(self, user_id: int) -> list[dict]:
        """
        Conversations where this user is a participant.
        """
        url = f"{self.base_url}/conversations/"
        resp = requests.get(
            url, params={"participant": user_id}, headers=self._headers()
        )
        data = self._handle_response(resp)
        return data if isinstance(data, list) else []

    def delete_conversation(self, conversation_id: int) -> bool:
        url = f"{self.base_url}/conversations/{conversation_id}/"
        resp = requests.delete(url, headers=self._headers())
        return resp.status_code in (200, 204)

    # ---------------------------
    # Admin- and analytics-style helpers
    # ---------------------------
    def is_admin(self) -> bool:
        return "admin" in (self.roles or []) or self.primary_role == "admin"

    def get_admin_dashboard_stats(self) -> Dict[str, int]:
        try:
            messages = self.get_all_messages()

            total = len(messages)
            critical = sum(
                1 for m in messages
                if m.get("priority", "").lower() == "urgent"
            )
            pending = sum(
                1 for m in messages
                if m.get("status", "").lower() == "pending"
            )
            resolved = sum(
                1 for m in messages
                if m.get("status", "").lower() == "resolved"
                and self._is_today(m.get("updated_at", ""))
            )

            return {
                "total_messages": total,
                "critical_issues": critical,
                "pending_responses": pending,
                "resolved_today": resolved,
            }
        except Exception as e:
            print("[DataManager] get_admin_dashboard_stats error:", e)
            return {
                "total_messages": 0,
                "critical_issues": 0,
                "pending_responses": 0,
                "resolved_today": 0,
            }

    def get_admin_messages(
            self,
            priority_filter: Optional[str] = None,
            status_filter: Optional[str] = None,
            department_filter: Optional[str] = None,
            search_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        messages = self.get_all_messages()
        filtered = messages

        if priority_filter and priority_filter != "All Priorities":
            priority_map = {
                "Urgent": "urgent",
                "High": "high",
                "Normal": "normal",
            }
            target_priority = priority_map.get(
                priority_filter, priority_filter.lower()
            )
            filtered = [
                m for m in filtered
                if m.get("priority", "").lower() == target_priority
            ]

        if status_filter and status_filter != "All Status":
            status_map = {
                "Pending": "pending",
                "Sent": "sent",
                "Resolved": "resolved",
            }
            target_status = status_map.get(
                status_filter, status_filter.lower()
            )
            filtered = [
                m for m in filtered
                if m.get("status", "").lower() == target_status
            ]

        if department_filter and department_filter != "All Departments":
            filtered = [
                m for m in filtered
                if m.get("department", "").lower()
                   == department_filter.lower()
            ]

        if search_query:
            search_lower = search_query.lower()
            filtered = [
                m for m in filtered
                if search_lower in m.get("subject", "").lower()
                   or search_lower in m.get("content", "").lower()
                   or search_lower in m.get("sender_name", "Unknown").lower()
            ]

        filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return filtered

    def get_critical_issues(self) -> List[Dict[str, Any]]:
        return self.get_admin_messages(priority_filter="Urgent")

    def get_pending_messages(self) -> List[Dict[str, Any]]:
        return self.get_admin_messages(status_filter="Pending")

    def get_system_issues(self) -> List[Dict[str, Any]]:
        messages = self.get_all_messages()
        return [
            m for m in messages
            if "system" in m.get("subject", "").lower()
               or "system" in m.get("content", "").lower()
        ]

    def get_technical_support(self) -> List[Dict[str, Any]]:
        messages = self.get_all_messages()
        return [
            m for m in messages
            if "technical" in m.get("subject", "").lower()
               or "technical" in m.get("content", "").lower()
        ]

    def get_user_activity_report(self, days: int = 7) -> Dict[str, Any]:
        try:
            messages = self.get_all_messages()
            cutoff_date = datetime.now() - timedelta(days=days)

            recent_messages = [
                m for m in messages
                if self._parse_date(m.get("created_at", "")) >= cutoff_date
            ]

            sender_counts: Dict[str, int] = {}
            dept_counts: Dict[str, int] = {}

            for msg in recent_messages:
                sender = msg.get("sender_name", "Unknown")
                dept = msg.get("department", "General")

                sender_counts[sender] = sender_counts.get(sender, 0) + 1
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

            most_active = (
                max(sender_counts.items(), key=lambda x: x[1])[0]
                if sender_counts else "N/A"
            )

            return {
                "total_messages_sent": len(recent_messages),
                "active_users": len(sender_counts),
                "most_active_user": most_active,
                "messages_by_department": dept_counts,
                "period_days": days,
            }
        except Exception as e:
            print("[DataManager] get_user_activity_report error:", e)
            return {
                "total_messages_sent": 0,
                "active_users": 0,
                "most_active_user": "N/A",
                "messages_by_department": {},
                "period_days": days,
            }

    def get_message_response_time_stats(self) -> Dict[str, Any]:
        try:
            messages = self.get_all_messages()
            response_times: List[float] = []

            for msg in messages:
                created = self._parse_date(msg.get("created_at", ""))
                updated = self._parse_date(msg.get("updated_at", ""))

                if created and updated:
                    delta = updated - created
                    hours = delta.total_seconds() / 3600
                    response_times.append(hours)

            if not response_times:
                return {
                    "avg_response_time_hours": 0,
                    "fastest_response_hours": 0,
                    "slowest_response_hours": 0,
                }

            return {
                "avg_response_time_hours": sum(response_times) / len(response_times),
                "fastest_response_hours": min(response_times),
                "slowest_response_hours": max(response_times),
            }
        except Exception as e:
            print("[DataManager] get_message_response_time_stats error:", e)
            return {
                "avg_response_time_hours": 0,
                "fastest_response_hours": 0,
                "slowest_response_hours": 0,
            }

    def send_system_broadcast(
            self, title: str, content: str
    ) -> Optional[Dict[str, Any]]:
        try:
            broadcast_data = {
                "subject": f"[SYSTEM] {title}",
                "content": content,
                "message_type": "broadcast",
                "priority": "high",
                "department": "System",
                "is_broadcast": True,
            }
            print("[DataManager] send_system_broadcast payload:", broadcast_data)

            url = f"{self.base_url}/messages/"
            print("[DataManager] POST", url)

            resp = requests.post(url, json=broadcast_data, headers=self._headers(), timeout=10)
            print("[DataManager] send_system_broadcast status:", resp.status_code)
            print("[DataManager] send_system_broadcast response:", resp.text[:500])

            self._messages_cache = None

            data = self._handle_response(resp)
            print("[DataManager] send_system_broadcast parsed data:", data)
            return data
        except Exception as e:
            print("[DataManager] send_system_broadcast error:", e)
            return None


    def get_department_stats(self) -> Dict[str, int]:
        try:
            messages = self.get_all_messages()
            dept_counts: Dict[str, int] = {}

            for msg in messages:
                dept = msg.get("department", "General")
                dept_counts[dept] = dept_counts.get(dept, 0) + 1

            return dept_counts
        except Exception as e:
            print("[DataManager] get_department_stats error:", e)
            return {}

    # ---------------------------
    # Date helpers
    # ---------------------------
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

    def _is_today(self, date_str: str) -> bool:
        date = self._parse_date(date_str)
        if not date:
            return False
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        return today <= date < tomorrow

    def get_broadcast_messages(self) -> list[dict]:
        """
        Return all system broadcast messages visible to the current user.
        Assumes backend supports /messages/?message_type=broadcast
        and does NOT restrict by receiver.
        """
        url = f"{self.base_url}/messages/"
        resp = requests.get(
            url,
            params={"message_type": "broadcast"},
            headers=self._headers(),
            timeout=10,
        )
        data = self._handle_response(resp)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data.get("results", [])
        return []

    class DataManager:
        ...

    def send_system_broadcast(self, title: str, content: str) -> Optional[Dict[str, Any]]:
        """
        Create a global system broadcast message.

        Backend exposes it to all authenticated users via MessageViewSet
        (is_broadcast=True, message_type='broadcast').
        """
        try:
            broadcast_data = {
                "subject": f"[SYSTEM] {title}",
                "content": content,
                "message_type": "broadcast",
                "priority": "high",
                "department": "System",
                "is_broadcast": True,
            }
            result = self.create_message(broadcast_data)
            # Invalidate cache so new broadcast appears in subsequent loads
            self._messages_cache = None
            return result
        except Exception as e:
            print("[DataManager] send_system_broadcast error:", e)
            return None


    def send_system_broadcast(
                self, title: str, content: str
        ) -> Optional[Dict[str, Any]]:
        """
        Create a global system broadcast message.

        Backend exposes it to all authenticated users
        via /api/broadcasts/ (or /api/messages/ with filters).
        """
        try:
            broadcast_data = {
                "subject": f"[SYSTEM] {title}",
                "content": content,
                "message_type": "broadcast",
                "priority": "high",
                "department": "System",
                "is_broadcast": True,
            }
            result = self.create_message(broadcast_data)
            # Invalidate cache so new broadcast appears in subsequent loads
            self._messages_cache = None
            return result
        except Exception as e:
            print("[DataManager] send_system_broadcast error:", e)
            return None

    def get_broadcast_messages(self) -> list[dict]:
        """
        Fetch all broadcast messages.

        Uses dedicated /broadcasts/ endpoint (ListAPIView) which returns
        messages where is_broadcast=True and message_type='broadcast'.
        """
        url = f"{self.base_url}/broadcasts/"
        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                timeout=10,
            )
        except Exception as e:
            print("[DataManager] get_broadcast_messages error:", e)
            return []

        data = self._handle_response(resp)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "results" in data:
            return data.get("results", [])
        return []

    def get_message_summaries_for_user(self, user_id: int) -> list[dict]:
        if not user_id:
            return []

        try:
            data = getattr(self, "data", {})
            all_messages = data.get("messages", [])
            summaries: list[dict] = []

            for m in all_messages:
                if m.get("receiver") != user_id:
                    continue

                conv = m.get("conversation")
                conv_id = conv.get("id") if isinstance(conv, dict) else conv

                sender_name = m.get("sender_name") or "Unknown"
                sender_email = m.get("sender_email") or None

                msg_type = "groups" if m.get("conversation_type") == "group" else "all"
                read = m.get("is_read", False)

                summaries.append({
                    "id": m.get("id"),
                    "conversation": conv_id,
                    "subject": m.get("subject", "No Subject"),
                    "content": m.get("content", ""),
                    "sender_name": sender_name,
                    "sender_email": sender_email,
                    "type": msg_type,
                    "read": read,
                })

            summaries.sort(key=lambda x: x.get("id", 0), reverse=True)
            return summaries
        except Exception as e:
            print("[DataManager] get_message_summaries_for_user error:", e)
            return []
