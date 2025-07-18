"""
URL configuration for GoolStarProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include, re_path
# Imports para drf-spectacular
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


# Vista simple para health checks
def health_check(request):
    return HttpResponse("OK", content_type="text/plain")


# Vista simple para página principal (raíz)
def home(request):
    return HttpResponse(
        "<html><body><h1>GoolStar API</h1>"
        "<p>¡Bienvenido a la API de GoolStar!</p>"
        "<p>La documentación de la API está disponible en "
        "<a href='/api/schema/swagger-ui/'>Swagger UI</a>.</p>"
        "</body></html>",
        content_type="text/html"
    )


urlpatterns = [
    # Cambio: Usar una vista simple para la raíz en lugar de redirección
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),


    # Health check endpoint para Fly.io
    path('health/', health_check, name='health_check'),
    # URL para la API de espectáculos
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

]

# Configuración para servir archivos multimedia durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
