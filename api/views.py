"""
Punto de entrada para las vistas de la API de GoolStar.

Este archivo proporciona compatibilidad con el código existente, importando
las vistas desde sus respectivos módulos. Para nuevos desarrollos, se recomienda
importar directamente desde los módulos correspondientes en api.views.
"""

# Importamos todos los ViewSets desde el paquete de vistas
from .views import (
    CategoriaViewSet,
    EquipoViewSet,
    JugadorViewSet,
    JugadorDocumentoViewSet,
    JornadaViewSet,
    PartidoViewSet,
    GolViewSet,
    TarjetaViewSet,
    TorneoViewSet,
)

# Exportamos explícitamente los nombres para mantener compatibilidad con importaciones existentes
__all__ = [
    'CategoriaViewSet',
    'EquipoViewSet',
    'JugadorViewSet',
    'JugadorDocumentoViewSet',
    'JornadaViewSet',
    'PartidoViewSet',
    'GolViewSet',
    'TarjetaViewSet',
    'TorneoViewSet',
]
