from django.urls import re_path
from .consumer import UserStatusConsumer

websocket_urlpatterns = [
    re_path("ws/user-status/", UserStatusConsumer.as_asgi()),
]