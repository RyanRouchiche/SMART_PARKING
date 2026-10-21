from django.urls import path
from . import views

urlpatterns = [
    path('areas/', views.areas, name='areas'),
    path('coordinates/', views.coordinates, name='coordinates'),
    path('snapshots/', views.snapshots, name='snapshots'),
]
