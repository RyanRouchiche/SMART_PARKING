from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashbordviewAPI.as_view(), name='dashboard' ),
]