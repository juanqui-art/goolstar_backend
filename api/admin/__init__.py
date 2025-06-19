"""
Imports centralizados para mantener compatibilidad con código existente.
Este archivo importa todas las configuraciones de admin desde los módulos especializados.
"""

# Importar configuraciones base
from .base_admin import (
    CategoriaAdmin,
    TorneoAdmin,
    EquipoInlineTorneo,
    FaseEliminatoriaInline,
    FaseEliminatoriaAdmin,
    JornadaAdmin,
)

# Importar configuraciones de participantes
from .participantes_admin import (
    DirigenteAdmin,
    ArbitroAdmin,
    EquipoAdmin,
    JugadorAdmin,
    JugadorDocumentoAdmin,
    JugadorInline,
    JugadorDocumentoInline,
)

# Importar configuraciones de competición
from .competicion_admin import (
    PartidoAdmin,
    GolAdmin,
    TarjetaAdmin,
    CambioJugadorAdmin,
    EventoPartidoAdmin,
    ParticipacionJugadorAdmin,
    GolInline,
    TarjetaInline,
    CambioJugadorInline,
    PartidoForm,
    EquipoFilter,
)

# Importar configuraciones de estadísticas
from .estadisticas_admin import (
    EstadisticaEquipoAdmin,
    LlaveEliminatoriaAdmin,
    MejorPerdedorAdmin,
    EventoTorneoAdmin,
)

# Importar configuraciones financieras
from .financiero_admin import (
    TransaccionPagoAdmin,
    PagoArbitroAdmin,
)

# Lista de todas las clases de admin exportadas para facilitar el mantenimiento
__all__ = [
    # Base admin classes
    'CategoriaAdmin',
    'TorneoAdmin',
    'EquipoInlineTorneo',
    'FaseEliminatoriaInline',
    'FaseEliminatoriaAdmin',
    'JornadaAdmin',
    
    # Participantes admin classes
    'DirigenteAdmin',
    'ArbitroAdmin',
    'EquipoAdmin',
    'JugadorAdmin',
    'JugadorDocumentoAdmin',
    'JugadorInline',
    'JugadorDocumentoInline',
    
    # Competición admin classes
    'PartidoAdmin',
    'GolAdmin',
    'TarjetaAdmin',
    'CambioJugadorAdmin',
    'EventoPartidoAdmin',
    'ParticipacionJugadorAdmin',
    'GolInline',
    'TarjetaInline',
    'CambioJugadorInline',
    'PartidoForm',
    'EquipoFilter',
    
    # Estadísticas admin classes
    'EstadisticaEquipoAdmin',
    'LlaveEliminatoriaAdmin',
    'MejorPerdedorAdmin',
    'EventoTorneoAdmin',
    
    # Financiero admin classes
    'TransaccionPagoAdmin',
    'PagoArbitroAdmin',
]