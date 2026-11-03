from django.urls import path

from . import views

urlpatterns = [
    path('users/', views.OperatorListView.as_view(), name='users'),
    path('users/<uuid:user_id>/', views.OperatorDetailView.as_view(), name='user_detail'),
    path('parking/areas/', views.areas, name='areas'),
]
