from django.urls import path
from . import views

urlpatterns = [
    path('' , views.home , name='home'),
    path('video_feed', views.VideoStream , name='videoStream'),
]


