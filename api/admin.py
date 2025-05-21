from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.db import models
from django.utils import timezone

# Importaciones de modelos base
from .models.base import Categoria, Torneo, FaseEliminatoria
# Importaciones de modelos de competición
from .models.competicion import Jornada, Partido, Gol, Tarjeta, CambioJugador, EventoPartido
# Importaciones de modelos de estadísticas
from .models.estadisticas import EstadisticaEquipo, LlaveEliminatoria, MejorPerdedor, EventoTorneo
# Importaciones de modelos financieros
from .models.financiero import TransaccionPago, PagoArbitro
# Importaciones de modelos de participación
from .models.participacion import ParticipacionJugador
# Importaciones de modelos de participantes
from .models.participantes import Equipo, Jugador, Dirigente, Arbitro

# Configuración del sitio de administración
admin.site.site_header = 'GoolStar - Administración de Torneos'
admin.site.site_title = 'GoolStar Admin'
admin.site.index_title = 'Panel de administración de torneos'


# -----------------------------------------------------------------------------
# CONFIGURACIONES BÁSICAS
# -----------------------------------------------------------------------------

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

        grupos = {}
        for letra in ['A', 'B', 'C', 'D'][:obj.numero_grupos]:
            grupos[letra] = obj.equipos.filter(grupo=letra, activo=True).count()

        return " | ".join([f"Grupo {g}: {c}" for g, c in grupos.items()])

    equipos_por_grupo.short_description = "Equipos por grupo"


@admin.register(FaseEliminatoria)
class FaseEliminatoriaAdmin(admin.ModelAdmin):
    list_display = ('torneo', 'nombre', 'orden', 'fecha_inicio', 'fecha_fin', 'completada')
    list_filter = ('torneo', 'completada')
    search_fields = ('nombre',)


@admin.register(Jornada)
class JornadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero', 'fecha')
    list_filter = ('fecha',)


# -----------------------------------------------------------------------------
# PARTICIPANTES
# -----------------------------------------------------------------------------

@admin.register(Dirigente)
class DirigenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono')
    search_fields = ('nombre', 'telefono')


@admin.register(Arbitro)
class ArbitroAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombres', 'apellidos', 'telefono')


class JugadorInline(admin.TabularInline):
    model = Jugador
    fields = ('primer_nombre', 'primer_apellido', 'cedula', 'posicion', 'numero_dorsal')
    extra = 1
    show_change_link = True


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'torneo', 'grupo', 'nivel', 'activo', 'deuda_total', 'numero_jugadores')
    list_filter = ('categoria', 'torneo', 'activo', 'grupo')
    search_fields = ('nombre',)
    list_select_related = ('categoria', 'torneo')  # Optimización para evitar N+1 queries
    inlines = [JugadorInline]
    actions = ['descargar_lista_jugadores_pdf', 'descargar_historial_partidos_pdf']

    fieldsets = (
        ('Información básica', {
            'fields': ('nombre', 'categoria', 'torneo', 'dirigente')
        }),
        ('Configuración de grupo', {
            'fields': ('grupo',),
            'description': 'Asigna el equipo a su grupo correspondiente (A, B, etc.)'
        }),
        ('Detalles del equipo', {
            'fields': ('logo', 'color_principal', 'color_secundario', 'nivel')
        }),
        ('Estado', {
            'fields': ('activo', 'inasistencias', 'excluido_por_inasistencias')
        }),
        ('Progreso', {
            'fields': ('clasificado_fase_grupos', 'fase_actual', 'eliminado_en_fase'),
            'classes': ('collapse',)
        }),
    )
    
    def numero_jugadores(self, obj):
        """Muestra el número de jugadores y lo resalta en rojo si excede 12"""
        count = obj.jugadores.count()
        if count > 12:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return count
    
    numero_jugadores.short_description = "Jugadores"
    numero_jugadores.admin_order_field = 'jugadores__count'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            jugadores__count=models.Count('jugadores')
        )
        return queryset
    
    def descargar_lista_jugadores_pdf(self, request, queryset):
        """Genera un PDF con la lista de jugadores del equipo seleccionado"""
        if len(queryset) != 1:
            self.message_user(request, "Por favor seleccione solo un equipo a la vez para descargar la lista", level='WARNING')
            return
            
        equipo = queryset.first()
        
        # Obtener jugadores del equipo
        jugadores = equipo.jugadores.all().order_by('numero_dorsal')
        
        # Preparar contexto para la plantilla
        context = {
            'equipo': equipo,
            'jugadores': jugadores,
            'fecha_actual': timezone.now().date(),
        }
        
        # Renderizar plantilla a HTML
        template = get_template('admin/equipos/lista_jugadores_pdf.html')
        html = template.render(context)
        
        # Crear PDF a partir del HTML
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            # Configurar respuesta HTTP con PDF
            filename = f"Lista_Jugadores_{equipo.nombre}_{timezone.now().strftime('%Y%m%d')}.pdf"
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        self.message_user(request, "Error al generar PDF", level='ERROR')
        return None
        
    descargar_lista_jugadores_pdf.short_description = "Descargar lista de jugadores en PDF"
    
    def descargar_historial_partidos_pdf(self, request, queryset):
        """Genera un PDF con el historial de partidos del equipo seleccionado, ordenados por fecha"""
        if len(queryset) != 1:
            self.message_user(request, "Por favor seleccione solo un equipo a la vez para descargar el historial", level='WARNING')
            return
            
        equipo = queryset.first()
        
        # Obtener todos los partidos donde participó el equipo (como local o visitante)
        partidos = Partido.objects.filter(
            models.Q(equipo_1=equipo) | models.Q(equipo_2=equipo)
        ).order_by('fecha')
        
        # Preparar contexto para la plantilla
        context = {
            'equipo': equipo,
            'partidos': partidos,
            'fecha_actual': timezone.now().date(),
        }
        
        # Renderizar plantilla a HTML
        template = get_template('admin/equipos/historial_partidos_pdf.html')
        html = template.render(context)
        
        # Crear PDF a partir del HTML
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            # Configurar respuesta HTTP con PDF
            filename = f"Historial_Partidos_{equipo.nombre}_{timezone.now().strftime('%Y%m%d')}.pdf"
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        self.message_user(request, "Error al generar el PDF", level='ERROR')
    
    descargar_historial_partidos_pdf.short_description = "Descargar historial de partidos en PDF fase grupos"


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cedula', 'equipo', 'numero_dorsal', 'posicion')
    list_filter = ('equipo__categoria', 'equipo', 'equipo__torneo')
    search_fields = ('primer_nombre', 'primer_apellido', 'cedula')
    ordering = ('primer_apellido',)
    list_per_page = 25
    list_select_related = ('equipo',)  # Optimización para evitar N+1 queries
    list_editable = ('cedula',)  # Solo cedula será editable directamente en la lista

    fieldsets = (
        ('Datos personales', {
            'fields': ('primer_nombre', 'segundo_nombre', 'primer_apellido',
                       'segundo_apellido', 'cedula', 'fecha_nacimiento')
        }),
        ('Información deportiva', {
            'fields': ('equipo', 'numero_dorsal', 'nivel', 'posicion')
        }),
        ('Estado', {
            'fields': ('suspendido', 'partidos_suspension_restantes', 'fecha_fin_suspension'),
            'classes': ('collapse',)
        }),
    )


# -----------------------------------------------------------------------------
# PARTIDOS Y EVENTOS
# -----------------------------------------------------------------------------

class GolInline(admin.TabularInline):
    model = Gol
    extra = 1


class TarjetaInline(admin.TabularInline):
    model = Tarjeta
    extra = 1


class CambioJugadorInline(admin.TabularInline):
    model = CambioJugador
    extra = 1


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


from django.contrib.admin import SimpleListFilter

# Custom filter for teams in Partido admin
class EquipoFilter(SimpleListFilter):
    title = 'Filtrar por equipo'  # Título más claro en español
    parameter_name = 'equipo'
    
    def lookups(self, request, model_admin):
        # Get all teams involved in any matches - mantenemos la lógica de búsqueda igual
        equipos = Equipo.objects.filter(
            models.Q(partidos_como_local__isnull=False) | 
            models.Q(partidos_como_visitante__isnull=False)
        ).distinct().order_by('nombre')
        return [(str(equipo.id), equipo.nombre) for equipo in equipos]
    
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
    list_display = ('__str__', 'jornada', 'fecha', 'goles_equipo_1', 'goles_equipo_2', 'completado')
    list_filter = (EquipoFilter, 'jornada', 'completado', 'equipo_1__categoria', 'torneo', 'equipo_1__grupo', 'fase_eliminatoria')
    search_fields = ('equipo_1__nombre', 'equipo_2__nombre', 'arbitro__nombres', 'arbitro__apellidos', 'cancha')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_per_page = 25
    inlines = [GolInline, TarjetaInline, CambioJugadorInline]
    list_select_related = ('jornada', 'equipo_1', 'equipo_2', 'arbitro', 'torneo', 'fase_eliminatoria')
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
        ('Control de asistencia', {
            'fields': ('inasistencia_equipo_1', 'inasistencia_equipo_2', 'equipo_pone_balon')
        }),
        ('Acta', {
            'fields': ('observaciones', 'acta_firmada', 'acta_firmada_equipo_1', 'acta_firmada_equipo_2')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('equipo_1', 'equipo_2', 'jornada', 'torneo', 'arbitro')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filtra equipos por grupo si se está creando un partido nuevo"""
        if db_field.name == "equipo_1" and request.GET.get('grupo'):
            grupo = request.GET.get('grupo')
            kwargs["queryset"] = Equipo.objects.filter(grupo=grupo, activo=True)
        if db_field.name == "equipo_2" and request.GET.get('grupo'):
            grupo = request.GET.get('grupo')
            kwargs["queryset"] = Equipo.objects.filter(grupo=grupo, activo=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def marcar_como_completados(self, request, queryset):
        """Marca los partidos seleccionados como completados"""
        partidos_actualizados = queryset.update(completado=True)
        self.message_user(request, f"{partidos_actualizados} partidos han sido marcados como completados.")
    
    marcar_como_completados.short_description = "Marcar partidos como completados"


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

    def marcar_como_pagadas(self, request, queryset):
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


# -----------------------------------------------------------------------------
# ESTADÍSTICAS
# -----------------------------------------------------------------------------

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


# -----------------------------------------------------------------------------
# FINANZAS
# -----------------------------------------------------------------------------

@admin.register(TransaccionPago)
class TransaccionPagoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'tipo', 'fecha', 'monto', 'es_ingreso', 'concepto')
    list_filter = ('tipo', 'es_ingreso')
    search_fields = ('equipo__nombre', 'concepto')
    date_hierarchy = 'fecha'
    list_select_related = ('equipo', 'partido', 'tarjeta', 'jugador')  # Optimización para evitar N+1 queries


@admin.register(PagoArbitro)
class PagoArbitroAdmin(admin.ModelAdmin):
    list_display = ('arbitro', 'partido', 'equipo', 'monto', 'pagado')
    list_filter = ('pagado',)
    search_fields = ('arbitro__nombres', 'arbitro__apellidos')
    list_select_related = ('arbitro', 'partido', 'equipo')  # Optimización para evitar N+1 queries
    actions = ['marcar_como_pagados']

    def marcar_como_pagados(self, request, queryset):
        from django.utils import timezone
        queryset.update(pagado=True, fecha_pago=timezone.now())

    marcar_como_pagados.short_description = "Marcar pagos seleccionados como pagados"
