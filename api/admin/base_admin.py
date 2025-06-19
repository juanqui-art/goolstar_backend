"""
Configuraciones de administración para modelos base del sistema.
Incluye administración de Categorías, Torneos, Fases Eliminatorias y Jornadas.
"""

from django.contrib import admin
from django.db import models

# Importaciones de modelos base
from ..models.base import Categoria, Torneo, FaseEliminatoria
from ..models.competicion import Jornada
from ..models.participantes import Equipo

# Configuración del sitio de administración
admin.site.site_header = 'GoolStar - Administración de Torneos'
admin.site.site_title = 'GoolStar Admin'
admin.site.index_title = 'Panel de administración de torneos'


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'costo_inscripcion')
    search_fields = ('nombre',)

    def get_model_perms(self, request):
        """Devuelve los permisos para este modelo."""
        return {'view': True, 'add': True, 'change': True, 'delete': True}

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            ('Información básica', {
                'fields': ('nombre', 'descripcion')
            }),
            ('Costos', {
                'fields': ('costo_inscripcion', 'multa_amarilla', 'multa_roja', 'costo_arbitraje')
            }),
            ('Premios', {
                'fields': ('premio_primero', 'premio_segundo', 'premio_tercero', 'premio_cuarto'),
                'classes': ('collapse',)
            }),
            ('Configuración adicional', {
                'fields': ('limite_inasistencias', 'limite_amarillas_suspension', 'partidos_suspension_roja'),
                'classes': ('collapse',)
            }),
        ]
        return fieldsets


class EquipoInlineTorneo(admin.TabularInline):
    model = Equipo
    fields = ('nombre', 'grupo', 'activo')
    extra = 0
    can_delete = False
    show_change_link = True
    readonly_fields = ('nombre',)

    def has_add_permission(self, request, obj=None):
        return False


class FaseEliminatoriaInline(admin.TabularInline):
    model = FaseEliminatoria
    fields = ('nombre', 'orden', 'fecha_inicio', 'fecha_fin', 'completada')
    extra = 0
    show_change_link = True
    
    def get_queryset(self, request):
        """Optimize queryset for inline display"""
        return super().get_queryset(request).select_related('torneo')


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'fecha_inicio', 'fase_actual', 'activo', 'finalizado')
    list_filter = ('categoria', 'activo', 'finalizado')
    search_fields = ('nombre',)
    inlines = [EquipoInlineTorneo, FaseEliminatoriaInline]

    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'categoria', 'fecha_inicio', 'fecha_fin', 'activo', 'finalizado')
        }),
        ('Formato de competición', {
            'fields': ('tiene_fase_grupos', 'numero_grupos', 'equipos_clasifican_por_grupo',
                       'tiene_eliminacion_directa')
        }),
        ('Estado', {
            'fields': ('fase_actual',)
        }),
    )

    def equipos_por_grupo(self, obj):
        """Muestra la cantidad de equipos por grupo"""
        if not obj.tiene_fase_grupos:
            return "No aplica"

        # Optimize: Use single query with conditional aggregation instead of multiple queries
        grupos_conteo = obj.equipos.filter(activo=True).values('grupo').annotate(
            count=models.Count('id')
        ).order_by('grupo')
        
        # Convert to dict for easy lookup
        grupos_dict = {g['grupo']: g['count'] for g in grupos_conteo if g['grupo']}
        
        # Build result for configured number of groups
        resultado = []
        for letra in ['A', 'B', 'C', 'D'][:obj.numero_grupos]:
            count = grupos_dict.get(letra, 0)
            resultado.append(f"Grupo {letra}: {count}")

        return " | ".join(resultado)

    equipos_por_grupo.short_description = "Equipos por grupo"


@admin.register(FaseEliminatoria)
class FaseEliminatoriaAdmin(admin.ModelAdmin):
    list_display = ('torneo', 'nombre', 'orden', 'fecha_inicio', 'fecha_fin', 'completada')
    list_filter = ('torneo', 'completada')
    search_fields = ('nombre',)
    list_select_related = ('torneo',)  # Optimización para evitar N+1 queries


@admin.register(Jornada)
class JornadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero', 'fecha')
    list_filter = ('fecha',)