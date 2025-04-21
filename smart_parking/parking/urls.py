from django.urls import path
from . import views
import os
from django.conf import settings
from django.conf.urls.static import static




urlpatterns = [
    path('api/pickupSpot/', views.pick_up_spot_api, name='PickUpSpot'),
    path('api/saveSpotCoordinates/', views.save_spot_coordinates_api, name='SaveSpotCoordinates'),
    path('api/video/', views.stream_page, name='video-stream'),
    path('api/floors/', views.get_available_floors, name='get_available_floors'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

