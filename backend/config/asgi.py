"""
ASGI config for backend project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.Messaging.routing import websocket_urlpatterns  # import your WS patterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")  # adjust if needed

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
