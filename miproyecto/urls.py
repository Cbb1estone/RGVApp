from django.contrib import admin
from django.urls import path, include 

urlpatterns = [
    path('admin/', admin.site.get_admin_urls() if hasattr(admin.site, 'get_admin_urls') else admin.site.urls),
    path('', include('tesoreria.urls')), 
    path('accounts/', include('django.contrib.auth.urls')),
]