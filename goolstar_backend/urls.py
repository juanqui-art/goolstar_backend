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
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.http import HttpResponse

# Imports para drf-yasg (Swagger)
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Configuración del esquema de Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="GoolStar API",
        default_version='v1',
        description="API para gestión de competiciones deportivas",
        terms_of_service="https://www.goolstar.com/terms/",
        contact=openapi.Contact(email="contact@goolstar.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Vista simple para health checks
def health_check(request):
    return HttpResponse("OK", content_type="text/plain")

# Vista simple para página principal (raíz)
def home(request):
    return HttpResponse(
        "<html><body><h1>GoolStar API</h1>"
        "<p>¡Bienvenido a la API de GoolStar!</p>"
        "<p>La documentación de la API está disponible en "
        "<a href='/swagger/'>Swagger</a> o <a href='/redoc/'>ReDoc</a>.</p>"
        "</body></html>",
        content_type="text/html"
    )

urlpatterns = [
    # Cambio: Usar una vista simple para la raíz en lugar de redirección
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    
    # URLs para la documentación con Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # Health check endpoint para Fly.io
    path('health/', health_check, name='health_check'),
]

# Configuración para servir archivos multimedia durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Añadir URLs de Debug Toolbar cuando DEBUG está activado
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
