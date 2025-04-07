from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.urls import path
from . import views

urlpatterns = [

    path('login/', views.loginviewAPI, name='login'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('users-infos/', views.getInfoUsers, name='get_user_info'),
    path('logout/', views.logout, name='logout'),
    path('register/', views.register, name='register'),
    path('dashbord/', views.dashbordviewAPI, name='dashbord'),
]