from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/public/v1/', include('public.urls')),
    path('api/', include('users.urls')),
    path('api/', include('parking.urls')),
    path('api/', include('camera.urls')),
    re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
