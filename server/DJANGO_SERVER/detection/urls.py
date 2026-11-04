from django.urls import path

from . import views

urlpatterns = [
    path('parking/stats/', views.StatsView.as_view(), name='parking_stats'),
]
