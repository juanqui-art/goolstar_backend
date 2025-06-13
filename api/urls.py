from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, EquipoViewSet, JugadorViewSet, JugadorDocumentoViewSet,
    JornadaViewSet, PartidoViewSet, GolViewSet, TarjetaViewSet, TorneoViewSet
)
from .auth import CustomTokenObtainPairView, RegistroUsuarioView
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'equipos', EquipoViewSet)
router.register(r'jugadores', JugadorViewSet)
router.register(r'jugador-documentos', JugadorDocumentoViewSet, basename='jugadordocumento')
router.register(r'jornadas', JornadaViewSet)
router.register(r'partidos', PartidoViewSet)
router.register(r'goles', GolViewSet)
router.register(r'tarjetas', TarjetaViewSet)
router.register(r'torneos', TorneoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Rutas de autenticación JWT
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/registro/', RegistroUsuarioView.as_view(), name='registro_usuario'),
]
