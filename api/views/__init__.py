"""
Módulos de vistas organizados por dominio para la API de GoolStar.

Este paquete contiene ViewSets separados por dominio funcional, 
mejorando la organización del código y facilitando el mantenimiento.
"""

# Importaciones explícitas para mantener compatibilidad con el código existente
from .categoria_views import CategoriaViewSet
from .equipo_views import EquipoViewSet
from .jugador_views import JugadorViewSet
from .jornada_views import JornadaViewSet
from .partido_views import PartidoViewSet
from .gol_views import GolViewSet
from .tarjeta_views import TarjetaViewSet
from .torneo_views import TorneoViewSet

# Mantener todas las clases exportadas en __all__ para facilitar imports
__all__ = [
    'CategoriaViewSet',
    'EquipoViewSet',
    'JugadorViewSet',
    'JornadaViewSet',
    'PartidoViewSet',
    'GolViewSet',
    'TarjetaViewSet',
    'TorneoViewSet',
]
