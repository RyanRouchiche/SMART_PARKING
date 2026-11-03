from django.urls import path

from . import views

urlpatterns = [
    path('cameras/', views.CameraListView.as_view(), name='cameras'),
    path('cameras/<uuid:camera_id>/', views.CameraDetailView.as_view(), name='camera_detail'),
    path('parking/coordinates/', views.coordinates, name='coordinates'),
    path('parking/snapshots/', views.snapshots, name='snapshots'),
]
