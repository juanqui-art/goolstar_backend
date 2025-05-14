from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet, EquipoViewSet, JugadorViewSet, JornadaViewSet,
    PartidoViewSet, GolViewSet, TarjetaViewSet, TorneoViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'equipos', EquipoViewSet)
router.register(r'jugadores', JugadorViewSet)
router.register(r'jornadas', JornadaViewSet)
router.register(r'partidos', PartidoViewSet)
router.register(r'goles', GolViewSet)
router.register(r'tarjetas', TarjetaViewSet)
router.register(r'torneos', TorneoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
