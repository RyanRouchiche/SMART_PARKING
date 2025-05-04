from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from . import views



urlpatterns = [
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', views.CustomObtainRefreshToken.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterAPIView.as_view(), name='register'),
    path('activate/<uidb64>/<token>/', views.ActivateUserAPIView.as_view(), name='activate'),
]