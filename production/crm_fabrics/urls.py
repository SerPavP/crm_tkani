from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_login(request):
    return redirect('core:login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls')),
    path('', redirect_to_login),
    path('core/', include('core.urls')),
    path('deals/', include('deals.urls')),
    path('clients/', include('clients.urls')),
    path('fabrics/', include('fabrics.urls')),
    path('warehouse/', include('warehouse.urls')),
    path('finances/', include('finances.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


