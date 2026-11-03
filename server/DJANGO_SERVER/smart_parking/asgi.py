import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from django.conf import settings


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_parking.settings')


django_asgi_app = get_asgi_application()

from parking.routing import websocket_urlpatterns as presence_websocket_urlpatterns
from detection.routing import websocket_urlpatterns as video_websocket_urlpatterns


def origin_check(app):
    if settings.WS_ALLOWED_ORIGINS:
        return OriginValidator(app, settings.WS_ALLOWED_ORIGINS)
    return AllowedHostsOriginValidator(app)


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": origin_check(
        AuthMiddlewareStack(
            URLRouter(
                presence_websocket_urlpatterns + video_websocket_urlpatterns
            )
        )
    ),
})
