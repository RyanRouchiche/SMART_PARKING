from django.urls import path
from . import views
import os
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include


urlpatterns = [
    path('pickupSpot/', views.pick_up_spot_api, name='PickUpSpot'),
    path('saveSpotCoordinates/', views.save_spot_coordinates_api, name='SaveSpotCoordinates'),
    path('video/', views.stream_page.as_view(), name='video-stream'),
    path('areas/', views.get_available_areas, name='get_available_areas'),
    path('camera/' , include('camera.urls')),
    path('coordinates/', views.get_jsonFile, name='get_jsonFile'), 
    path('test/', views.test.as_view(), name='test'), 
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

