# Imports centralizados para mantener compatibilidad con código existente

# Serializers base
from .base_serializers import (
    CategoriaSerializer,
    TorneoSerializer,
    TorneoDetalleSerializer,
    TorneoListSerializer,
    JornadaSerializer,
)

# Serializers de participantes
from .participantes_serializers import (
    EquipoSerializer,
    EquipoDetalleSerializer,
    EquipoListSerializer,
    JugadorSerializer,
    JugadorListSerializer,
    JugadorConDocumentosSerializer,
)

# Serializers de competición
from .competicion_serializers import (
    PartidoSerializer,
    PartidoDetalleSerializer,
    PartidoListSerializer,
    GolSerializer,
    GolListSerializer,
    TarjetaSerializer,
    TarjetaListSerializer,
)

# Serializers de estadísticas
from .estadisticas_serializers import (
    EstadisticaEquipoSerializer,
    EstadisticaEquipoListSerializer,
    TablaposicionesSerializer,
    TablaposicionesOptimizadaSerializer,
)

# Serializers de documentos
from .documentos_serializers import (
    JugadorDocumentoSerializer,
    JugadorDocumentoListSerializer,
    JugadorDocumentoUploadSerializer,
    JugadorDocumentoVerificationSerializer,
)

# Lista de todos los serializers para referencia
__all__ = [
    # Base
    'CategoriaSerializer',
    'TorneoSerializer',
    'TorneoDetalleSerializer', 
    'TorneoListSerializer',
    'JornadaSerializer',
    
    # Participantes
    'EquipoSerializer',
    'EquipoDetalleSerializer',
    'EquipoListSerializer',
    'JugadorSerializer',
    'JugadorListSerializer',
    'JugadorConDocumentosSerializer',
    
    # Competición
    'PartidoSerializer',
    'PartidoDetalleSerializer',
    'PartidoListSerializer',
    'GolSerializer',
    'GolListSerializer',
    'TarjetaSerializer',
    'TarjetaListSerializer',
    
    # Estadísticas
    'EstadisticaEquipoSerializer',
    'EstadisticaEquipoListSerializer',
    'TablaposicionesSerializer',
    'TablaposicionesOptimizadaSerializer',
    
    # Documentos
    'JugadorDocumentoSerializer',
    'JugadorDocumentoListSerializer',
    'JugadorDocumentoUploadSerializer',
    'JugadorDocumentoVerificationSerializer',
]