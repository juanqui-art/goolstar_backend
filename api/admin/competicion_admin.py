"""
Configuraciones de administración para modelos de competición.
Incluye administración de Partidos, Goles, Tarjetas, Cambios y Eventos.
"""

from django import forms
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from django.db import models

# Importaciones de modelos de competición
from ..models.competicion import Partido, Gol, Tarjeta, CambioJugador, EventoPartido
from ..models.participacion import ParticipacionJugador
from ..models.participantes import Jugador, Equipo


class GolInline(admin.TabularInline):
    model = Gol
    extra = 1
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Solo filtramos si estamos editando un Partido existente y el campo es 'jugador'
        if db_field.name == "jugador":
            # Intentamos obtener el ID del partido desde la URL
            partido_id = request.resolver_match.kwargs.get('object_id')
            if partido_id:
                try:
                    partido = Partido.objects.get(pk=partido_id)
                    # Filtramos jugadores que pertenecen a los equipos del partido
                    kwargs["queryset"] = Jugador.objects.filter(
                        equipo__in=[partido.equipo_1, partido.equipo_2]
                    ).select_related('equipo').order_by('equipo__nombre', 'primer_apellido')
                except Partido.DoesNotExist:
                    pass  # Si no existe el partido, no filtramos
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class TarjetaInline(admin.TabularInline):
    model = Tarjeta
    extra = 1
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Solo filtramos si estamos editando un Partido existente y el campo es 'jugador'
        if db_field.name == "jugador":
            # Intentamos obtener el ID del partido desde la URL
            partido_id = request.resolver_match.kwargs.get('object_id')
            if partido_id:
                try:
                    partido = Partido.objects.get(pk=partido_id)
                    # Filtramos jugadores que pertenecen a los equipos del partido
                    kwargs["queryset"] = Jugador.objects.filter(
                        equipo__in=[partido.equipo_1, partido.equipo_2]
                    ).select_related('equipo').order_by('equipo__nombre', 'primer_apellido')
                except Partido.DoesNotExist:
                    pass  # Si no existe el partido, no filtramos
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CambioJugadorInline(admin.TabularInline):
    model = CambioJugador
    extra = 1
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Solo filtramos para los campos de jugadores
        if db_field.name in ["jugador_sale", "jugador_entra"]:
            # Intentamos obtener el ID del partido desde la URL
            partido_id = request.resolver_match.kwargs.get('object_id')
            if partido_id:
                try:
                    partido = Partido.objects.get(pk=partido_id)
                    # Filtramos jugadores que pertenecen a los equipos del partido
                    kwargs["queryset"] = Jugador.objects.filter(
                        equipo__in=[partido.equipo_1, partido.equipo_2]
                    ).select_related('equipo').order_by('equipo__nombre', 'primer_apellido')
                except Partido.DoesNotExist:
                    pass  # Si no existe el partido, no filtramos
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class PartidoForm(forms.ModelForm):
    """Formulario personalizado para el modelo Partido con validación adicional"""

    class Meta:
        model = Partido
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        equipo_1 = cleaned_data.get('equipo_1')
        equipo_2 = cleaned_data.get('equipo_2')

        if not equipo_1:
            self.add_error('equipo_1', 'Debe seleccionar el primer equipo')

        if not equipo_2:
            self.add_error('equipo_2', 'Debe seleccionar el segundo equipo')

        if equipo_1 and equipo_2 and equipo_1 == equipo_2:
            self.add_error('equipo_2', 'Debe seleccionar equipos diferentes')

        return cleaned_data


# Custom filter for teams in Partido admin
class EquipoFilter(SimpleListFilter):
    title = 'Filtrar por equipo'  # Título más claro en español
    parameter_name = 'equipo'
    
    def lookups(self, request, model_admin):
        # Get all teams involved in any matches - optimized to use values_list for better performance
        equipos = Equipo.objects.filter(
            models.Q(partidos_como_local__isnull=False) | 
            models.Q(partidos_como_visitante__isnull=False)
        ).distinct().values_list('id', 'nombre').order_by('nombre')
        return [(str(equipo_id), nombre) for equipo_id, nombre in equipos]
    
    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        # Mantenemos la lógica de filtrado igual
        return queryset.filter(
            models.Q(equipo_1__id=self.value()) | 
            models.Q(equipo_2__id=self.value())
        )


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    form = PartidoForm
    list_display = ('__str__', 'jornada', 'fecha', 'goles_equipo_1', 'goles_equipo_2', 'completado', 'mostrar_victoria_default')
    list_filter = (EquipoFilter, 'jornada', 'completado', 'torneo', 'fase_eliminatoria', 'victoria_por_default')
    search_fields = ('equipo_1__nombre', 'equipo_2__nombre', 'arbitro__nombres', 'arbitro__apellidos', 'cancha')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_per_page = 25
    inlines = [GolInline, TarjetaInline, CambioJugadorInline]
    list_select_related = ('jornada', 'equipo_1', 'equipo_2', 'arbitro', 'torneo', 'fase_eliminatoria', 'equipo_ganador_default')
    actions = ['marcar_como_completados']
    
    
    fieldsets = (
        ('Información general', {
            'fields': ('torneo', 'jornada', 'fase_eliminatoria', 'fecha', 'arbitro', 'cancha')
        }),
        ('Equipos', {
            'fields': ('equipo_1', 'equipo_2'),
            'description': 'Ambos equipos son requeridos para crear un partido'
        }),
        ('Resultado', {
            'fields': ('goles_equipo_1', 'goles_equipo_2', 'completado', 'es_eliminatorio',
                       'penales_equipo_1', 'penales_equipo_2')
        }),
        ('Victoria por default', {
            'fields': ('victoria_por_default', 'equipo_ganador_default'),
            'description': 'Utilizar solo cuando un equipo gana sin jugar el partido normalmente (por retiro, inasistencia o sanción)'
        }),
        ('Control de asistencia', {
            'fields': ('inasistencia_equipo_1', 'inasistencia_equipo_2', 'equipo_pone_balon')
        }),
        ('Acta', {
            'fields': ('observaciones', 'acta_firmada', 'acta_firmada_equipo_1', 'acta_firmada_equipo_2')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related(
            'equipo_1', 'equipo_2', 'jornada', 'torneo', 'arbitro', 
            'equipo_ganador_default', 'fase_eliminatoria', 'equipo_pone_balon'
        )
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra equipos por grupo si se está creando un partido nuevo"""
        if db_field.name == "equipo_1" and request.GET.get('grupo'):
            grupo = request.GET.get('grupo')
            kwargs["queryset"] = Equipo.objects.filter(grupo=grupo, activo=True)
        if db_field.name == "equipo_2" and request.GET.get('grupo'):
            grupo = request.GET.get('grupo')
            kwargs["queryset"] = Equipo.objects.filter(grupo=grupo, activo=True)
        if db_field.name == "equipo_ganador_default":
            if hasattr(self, 'parent_obj') and self.parent_obj:
                # Limitar opciones a los equipos que participan en este partido
                kwargs["queryset"] = Equipo.objects.filter(
                    id__in=[self.parent_obj.equipo_1.id, self.parent_obj.equipo_2.id]
                )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def marcar_como_completados(self, request, queryset):
        """Marca los partidos seleccionados como completados"""
        partidos_actualizados = queryset.update(completado=True)
        self.message_user(request, f"{partidos_actualizados} partidos han sido marcados como completados.")
    
    marcar_como_completados.short_description = "Marcar partidos como completados"
    
    def mostrar_victoria_default(self, obj):
        """Muestra visualmente si un partido tiene victoria por default"""
        if not obj.victoria_por_default:
            return ''
        
        motivos = {
            'retiro': 'Retiro',
            'inasistencia': 'Inasistencia',
            'sancion': 'Sanción'
        }
        
        equipo_ganador = obj.equipo_ganador_default.nombre if obj.equipo_ganador_default else "No especificado"
        motivo = motivos.get(obj.victoria_por_default, obj.victoria_por_default)
        
        return format_html(
            '<span style="color: #FF5733; font-weight: bold;">{}: {}</span>',
            motivo,
            equipo_ganador
        )
    
    mostrar_victoria_default.short_description = "Victoria por default"


@admin.register(Gol)
class GolAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'minuto')
    list_filter = ('partido__jornada', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')
    list_select_related = ('jugador', 'partido')  # Optimización para evitar N+1 queries


@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'tipo', 'pagada', 'monto_multa')
    list_filter = ('tipo', 'pagada', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')
    list_select_related = ('jugador', 'partido')  # Optimización para evitar N+1 queries
    actions = ['marcar_como_pagadas']

    def marcar_como_pagadas(self, _, queryset):
        queryset.update(pagada=True)

    marcar_como_pagadas.short_description = "Marcar tarjetas seleccionadas como pagadas"


@admin.register(CambioJugador)
class CambioJugadorAdmin(admin.ModelAdmin):
    list_display = ('partido', 'jugador_sale', 'jugador_entra', 'minuto')
    list_filter = ('partido__jornada',)
    search_fields = ('jugador_sale__primer_apellido', 'jugador_entra__primer_apellido')
    list_select_related = ('partido', 'jugador_sale', 'jugador_entra')  # Optimización para evitar N+1 queries


@admin.register(EventoPartido)
class EventoPartidoAdmin(admin.ModelAdmin):
    list_display = ('partido', 'tipo', 'minuto', 'equipo_responsable')
    list_filter = ('tipo',)
    search_fields = ('descripcion',)
    list_select_related = ('partido', 'equipo_responsable')  # Optimización para evitar N+1 queries


@admin.register(ParticipacionJugador)
class ParticipacionJugadorAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'es_titular', 'numero_dorsal', 'minuto_entra', 'minuto_sale')
    list_filter = ('es_titular', 'partido__jornada')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')
    list_select_related = ('jugador', 'partido')  # Optimización para evitar N+1 queries