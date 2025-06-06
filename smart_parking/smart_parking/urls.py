from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import LoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('parking/', include('parking.urls')),
    path('auth/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('camera/', include('camera.urls')),
    path('', LoginView.as_view(), name='login'), 
    path('i18n/', include('django.conf.urls.i18n')),
]   

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
