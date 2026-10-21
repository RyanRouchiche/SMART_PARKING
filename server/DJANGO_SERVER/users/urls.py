from django.urls import path
from . import views

urlpatterns = [
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/refresh/', views.RefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/activate/<uidb64>/<token>/', views.ActivateView.as_view(), name='activate'),
    path('auth/me/', views.MeView.as_view(), name='me'),
    path('users/', views.UserListView.as_view(), name='users'),
    path('users/<uuid:user_id>/', views.UserDetailView.as_view(), name='user_detail'),
]
