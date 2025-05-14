from django.urls import path 
from . import views
from users.views import GuestViewAPI ,  ListUserViewAPI , DeleteeUserViewAPI



urlpatterns = [
    path('', views.DashbordviewAPI.as_view(), name='dashboard' ),
    path('create-guest/', GuestViewAPI.as_view(), name='create_guest' ),
    path('users/users-list/', ListUserViewAPI.as_view(), name='users-list'),
    path('users/<uuid:user_id>/delete/', DeleteeUserViewAPI.as_view(), name='delete_user'),
    path('Forms/',views.FormsAPI.as_view(),name='Forms' )
]