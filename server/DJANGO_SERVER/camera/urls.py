from django.urls import path
from . import views

urlpatterns = [
    path('', views.CameraListView.as_view(), name='cameras'),
    path('<uuid:camera_id>/', views.CameraDetailView.as_view(), name='camera_detail'),
]
