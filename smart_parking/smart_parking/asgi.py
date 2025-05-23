import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_parking.settings')


django_asgi_app = get_asgi_application()

from users.routing import websocket_urlpatterns  as user_websocket_urlpatterns
from parking.routing import websocket_urlpatterns as parking_websocket_urlpatterns


application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            user_websocket_urlpatterns + parking_websocket_urlpatterns 
        )
    ),
})
