from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users.views import LoginView
from django.conf.urls.i18n import i18n_patterns  # Ensure you import this

urlpatterns = [
    path('admin/', admin.site.urls),
    path('parking/', include('parking.urls')),
    path('auth/', include('users.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('camera/', include('camera.urls')),
    path('', LoginView.as_view(), name='login'), 
]   

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += path('i18n/', include('django.conf.urls.i18n')),  
