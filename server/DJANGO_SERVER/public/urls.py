from django.urls import path

from . import views

urlpatterns = [
    path('auth/register/', views.RegisterView.as_view(), name='public_register'),
    path('auth/login/', views.LoginView.as_view(), name='public_login'),
    path('auth/refresh/', views.RefreshView.as_view(), name='public_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='public_logout'),
    path('account/', views.AccountView.as_view(), name='public_account'),
    path('parkings/nearby/', views.NearbyView.as_view(), name='public_nearby'),
    path('parkings/<uuid:parking_id>/', views.ParkingDetailView.as_view(), name='public_parking'),
    path('eta/', views.EtaView.as_view(), name='public_eta'),
]
