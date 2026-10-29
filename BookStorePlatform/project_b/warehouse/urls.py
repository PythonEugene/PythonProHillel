from django.contrib import admin
from django.urls import path, include

from .health import health

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health, name='health'),
    path('api/', include('api.urls')),
]
