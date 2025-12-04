from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BroadcastConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for system-wide broadcasts and generic chat updates.

    This consumer does two things:

    1) Subscribes every connected client to the common "system_broadcasts" group.
       - Used for global system announcements (e.g., maintenance notices).
       - Events sent to this group must use:
            {
                "type": "broadcast_message",
                "data": {
                    "id": int,
                    "subject": str,
                    "content": str,
                    "created_at": iso-string,
                    ...
                }
            }

    2) Handles generic chat events:
       - Back-end code can send per-user or per-conversation events with:
            {
                "type": "chat_message",
                "data": {
                    "id": int,
                    "conversation_id": int,
                    "sender_id": int,
                    "receiver_id": int | None,
                    "content": str,
                    "created_at": iso-string,
                    ...
                }
            }

       - The consumer transforms these into a client-facing JSON payload that
         your PyQt code expects:
            {
                "type": "broadcast" | "message",
                "id": ...,
                "conversation": ...,
                "sender": ...,
                "receiver": ...,
                "content": ...,
                "created_at": ...,
                ...
            }
    """

    async def connect(self):
        """
        Called when a WebSocket connection is opened.

        - Assigns the shared group name "system_broadcasts".
        - Adds this channel to the group so it can receive broadcast messages.
        - Accepts the WebSocket connection.
        """
        self.group_name = "system_broadcasts"
        if self.channel_layer is not None:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Called when the WebSocket connection is closed.

        - Removes this channel from the "system_broadcasts" group.
        """
        if self.channel_layer is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def broadcast_message(self, event):
        print("[WS DEBUG] BroadcastConsumer.broadcast_message:", event)
        data = event.get("data", {}) or {}
        await self.send_json({
            "type": "broadcast",
            "id": data.get("id"),
            "subject": data.get("subject"),
            "content": data.get("content", ""),
            "created_at": data.get("created_at"),
        })

    async def chat_message(self, event):
        print("[WS DEBUG] BroadcastConsumer.chat_message:", event)
        data = event.get("data", {}) or {}
        await self.send_json({
            "type": "message",
            "id": data.get("id"),
            "conversation": data.get("conversation_id"),
            "sender": data.get("sender_id"),
            "receiver": data.get("receiver_id"),
            "sender_name": data.get("sender_name"),
            "content": data.get("content", ""),
            "priority": data.get("priority"),
            "department": data.get("department"),
            "status": data.get("status"),
            "created_at": data.get("created_at"),
        })


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """
    Optional per-user chat consumer.

    This consumer:

    - Authenticates the connecting user.
    - Subscribes them to:
        - Their personal group: "user_<id>" for direct messages.
        - The global "system_broadcasts" group for announcements.

    Back-end can then use:
        - group_send("user_<id>", {"type": "chat_message", "data": {...}})
        - group_send("system_broadcasts", {"type": "broadcast_message", "data": {...}})
    """

    async def connect(self):
        """
        Called when a WebSocket connection is opened.

        - Rejects unauthenticated users.
        - Adds this channel to:
            - "user_<id>" group for personal messages.
            - "system_broadcasts" group for global broadcasts.
        """
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close()
            return

        self.user_group = f"user_{user.id}"
        if self.channel_layer is not None:
            await self.channel_layer.group_add(self.user_group, self.channel_name)
            await self.channel_layer.group_add("system_broadcasts", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """
        Removes this channel from user-specific and broadcast groups on disconnect.
        """
        user = self.scope.get("user")
        if self.channel_layer is None or not user or not user.is_authenticated:
            return

        await self.channel_layer.group_discard(f"user_{user.id}", self.channel_name)
        await self.channel_layer.group_discard("system_broadcasts", self.channel_name)

    async def broadcast_message(self, event):
        """
        Relay system broadcast events to this user.

        Expected event format:
            {"type": "broadcast_message", "data": {...}}

        Sends JSON with type="broadcast" so PyQt routes it to its broadcast handler.
        """
        data = event.get("data", {}) or {}
        await self.send_json({"type": "broadcast", **data})

    async def chat_message(self, event):
        """
        Relay chat message events to this user.

        Expected event format:
<<<<<<< Updated upstream
            {"type": "chat_message", "data": {...}
=======
            {"type": "chat_message", "data": {...}}
>>>>>>> Stashed changes

        Sends JSON with type="message" and the original data included.
        """
        data = event.get("data", {}) or {}
        await self.send_json({"type": "message", **data})
