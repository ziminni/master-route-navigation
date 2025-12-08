"""
WebSocket routing for the Messaging app.

This module defines the URL patterns for WebSocket connections that are
handled by Django Channels. These patterns are consumed by URLRouter
inside the project's ASGI application.
"""

from django.urls import re_path
from .consumers import BroadcastConsumer


# List of WebSocket URL patterns for this app.
# These are NOT regular Django HTTP views; they are used by Channels'
# URLRouter to dispatch incoming WebSocket connections to consumers.
websocket_urlpatterns = [
    # Route:
    #   ws://<host>/ws/broadcasts/
    # This URL is handled by BroadcastConsumer.as_asgi(), which subscribes
    # the client to the "system_broadcasts" group and sends broadcast JSON
    # messages to all connected clients.
    re_path(r"ws/broadcasts/$", BroadcastConsumer.as_asgi()),
]
