from django.urls import path
from . import views
import os
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('config/' , views.ConfigViewAPI.as_view(), name='config'),
    path('list-cameras/' , views.CameraListAPI.as_view(), name='camera_list'),
    path('delete/<uuid:uuid>/' , views.CameraDeleteViewAPI.as_view(), name='camera_delete'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

