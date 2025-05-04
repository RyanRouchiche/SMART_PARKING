from django.urls import re_path
from . import consumers

# Modify to exclude the floor parameter
websocket_urlpatterns = [
    # re_path(r'ws/video_feed/$', consumers.VideoFeedConsumer.as_asgi())  # No floor parameter

    re_path(r'ws/video/(?P<area>\d+)/$', consumers.VideoFeedConsumer.as_asgi()),


]
