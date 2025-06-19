"""
Configuraciones de administración para modelos de estadísticas.
Incluye administración de Estadísticas, Llaves Eliminatorias, Mejores Perdedores y Eventos.
"""

from django.contrib import admin

# Importaciones de modelos de estadísticas
from ..models.estadisticas import EstadisticaEquipo, LlaveEliminatoria, MejorPerdedor, EventoTorneo


@admin.register(EstadisticaEquipo)
class EstadisticaEquipoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'torneo', 'partidos_jugados', 'partidos_ganados', 'puntos', 'goles_favor', 'goles_contra')
    list_filter = ('torneo',)
    search_fields = ('equipo__nombre',)
    list_select_related = ('equipo', 'torneo')  # Optimización para evitar N+1 queries
    readonly_fields = ('puntos', 'partidos_jugados', 'partidos_ganados', 'partidos_empatados', 'partidos_perdidos',
                       'goles_favor', 'goles_contra', 'diferencia_goles', 'tarjetas_amarillas', 'tarjetas_rojas')


@admin.register(LlaveEliminatoria)
class LlaveEliminatoriaAdmin(admin.ModelAdmin):
    list_display = ('fase', 'numero_llave', 'equipo_1', 'equipo_2', 'completada')
    list_filter = ('fase', 'completada')
    list_select_related = ('fase', 'equipo_1', 'equipo_2', 'partido')  # Optimización para evitar N+1 queries


@admin.register(MejorPerdedor)
class MejorPerdedorAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'torneo', 'grupo', 'puntos', 'diferencia_goles')
    list_filter = ('torneo', 'grupo')
    list_select_related = ('equipo', 'torneo')


@admin.register(EventoTorneo)
class EventoTorneoAdmin(admin.ModelAdmin):
    list_display = ('torneo', 'tipo', 'fecha', 'equipo_involucrado')
    list_filter = ('tipo', 'torneo')
    search_fields = ('descripcion',)
    list_select_related = ('torneo', 'equipo_involucrado')  # Optimización para evitar N+1 queries