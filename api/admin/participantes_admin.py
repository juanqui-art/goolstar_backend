"""
Configuraciones de administración para participantes del sistema.
Incluye administración de Dirigentes, Árbitros, Equipos, Jugadores y Documentos.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.db import models
from django.utils import timezone

# Importaciones de modelos de participantes
from ..models.participantes import Equipo, Jugador, Dirigente, Arbitro, JugadorDocumento
from ..models.competicion import Partido, Tarjeta


@admin.register(Dirigente)
class DirigenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono')
    search_fields = ('nombre', 'telefono')


@admin.register(Arbitro)
class ArbitroAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombres', 'apellidos', 'telefono')


class JugadorDocumentoInline(admin.TabularInline):
    """Inline para mostrar documentos de jugador en la página de edición del jugador"""
    model = JugadorDocumento
    fields = ('tipo_documento', 'archivo_documento', 'estado_verificacion', 'fecha_subida')
    readonly_fields = ('fecha_subida',)
    extra = 0
    show_change_link = True
    
    def get_queryset(self, request):
        """Optimizar queryset para inline display"""
        return super().get_queryset(request).select_related('jugador')


class JugadorInline(admin.TabularInline):
    model = Jugador
    fields = ('primer_nombre', 'primer_apellido', 'cedula', 'posicion', 'numero_dorsal')
    extra = 1
    show_change_link = True
    ordering = ('numero_dorsal', 'primer_apellido')  # Order by jersey number, then last name
    
    def get_queryset(self, request):
        """Optimize queryset for inline display"""
        return super().get_queryset(request).select_related('equipo')


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'torneo', 'grupo', 'nivel', 'activo', 'estado', 'deuda_total', 'numero_jugadores')
    list_filter = ('categoria', 'torneo', 'activo', 'estado', 'grupo')
    search_fields = ('nombre',)
    list_select_related = ('categoria', 'torneo', 'dirigente')  # Optimización para evitar N+1 queries
    list_prefetch_related = ('jugadores',)  # Prefetch jugadores para método numero_jugadores
    inlines = [JugadorInline]
    actions = ['descargar_lista_jugadores_pdf', 'descargar_historial_partidos_pdf', 'marcar_como_retirados', 'descargar_balance_financiero_pdf']

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
            'fields': ('activo', 'estado', 'fecha_retiro', 'inasistencias', 'excluido_por_inasistencias')
        }),
        ('Progreso', {
            'fields': ('clasificado_fase_grupos', 'fase_actual', 'eliminado_en_fase'),
            'classes': ('collapse',)
        }),
    )
    
    def numero_jugadores(self, obj):
        """Muestra el número de jugadores y lo resalta en rojo si excede 12"""
        # Use annotated count to avoid N+1 query
        count = getattr(obj, 'numero_jugadores_count', obj.jugadores.count())
        if count > 12:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', count)
        return count
    
    def marcar_como_retirados(self, request, queryset):
        """Marca los equipos seleccionados como retirados"""
        from django.utils import timezone
        fecha_actual = timezone.now()
        
        equipos_actualizados = 0
        for equipo in queryset:
            if equipo.estado != Equipo.Estado.RETIRADO:
                equipo.estado = Equipo.Estado.RETIRADO
                equipo.fecha_retiro = fecha_actual
                equipo.activo = False
                equipo.save()
                equipos_actualizados += 1
                
        self.message_user(
            request,
            f"{equipos_actualizados} equipo(s) han sido marcados como retirados."
        )
    marcar_como_retirados.short_description = "Marcar equipos seleccionados como retirados"
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            numero_jugadores_count=models.Count('jugadores', distinct=True)
        ).select_related('categoria', 'torneo', 'dirigente')
        return queryset
    
    def descargar_lista_jugadores_pdf(self, request, queryset):
        """Genera un PDF con la lista de jugadores del equipo seleccionado"""
        if len(queryset) != 1:
            self.message_user(request, "Por favor seleccione solo un equipo a la vez para descargar la lista", level='WARNING')
            return
            
        equipo = queryset.first()
        
        # Obtener jugadores del equipo - optimized with select_related
        jugadores = equipo.jugadores.select_related('equipo').all().order_by('numero_dorsal')
        
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
        # Optimized with select_related to avoid N+1 queries
        partidos = Partido.objects.filter(
            models.Q(equipo_1=equipo) | models.Q(equipo_2=equipo)
        ).select_related(
            'equipo_1', 'equipo_2', 'jornada', 'torneo', 'arbitro', 'fase_eliminatoria'
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

    def descargar_balance_financiero_pdf(self, request, queryset):
        """Genera un PDF con el balance financiero del equipo, incluyendo deudas por inscripción y tarjetas"""
        if len(queryset) != 1:
            self.message_user(request, "Por favor seleccione solo un equipo a la vez para descargar el balance financiero", level='WARNING')
            return

        from ..models.financiero import TransaccionPago
        from decimal import Decimal
            
        equipo = queryset.first()
        
        # Obtener datos de inscripción
        costo_inscripcion = equipo.categoria.costo_inscripcion or Decimal('0.00')
        abonos_inscripcion = TransaccionPago.objects.filter(
            equipo=equipo, 
            tipo='abono_inscripcion'
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0.00')
        saldo_inscripcion = costo_inscripcion - abonos_inscripcion
        
        # Obtener tarjetas pendientes de pago - optimized with single query and prefetch
        tarjetas_pendientes = Tarjeta.objects.filter(
            jugador__equipo=equipo, 
            pagada=False
        ).select_related('jugador', 'partido', 'jugador__equipo')
        
        # Separate by type using Python filtering to avoid additional queries
        tarjetas_amarillas = [t for t in tarjetas_pendientes if t.tipo == 'AMARILLA']
        tarjetas_rojas = [t for t in tarjetas_pendientes if t.tipo == 'ROJA']
        
        # Calcular totales
        total_amarillas = sum(t.monto_multa for t in tarjetas_amarillas)
        total_rojas = sum(t.monto_multa for t in tarjetas_rojas)
        deuda_total = saldo_inscripcion + total_amarillas + total_rojas
        
        # Preparar contexto para la plantilla
        context = {
            'equipo': equipo,
            'fecha_actual': timezone.now(),
            'costo_inscripcion': costo_inscripcion,
            'abonos_inscripcion': abonos_inscripcion,
            'saldo_inscripcion': saldo_inscripcion,
            'tarjetas_amarillas': tarjetas_amarillas,
            'tarjetas_rojas': tarjetas_rojas,
            'total_amarillas': total_amarillas,
            'total_rojas': total_rojas,
            'deuda_total': deuda_total
        }
        
        # Renderizar plantilla a HTML
        template = get_template('admin/balance_equipo_pdf.html')
        html = template.render(context)
        
        # Crear PDF a partir del HTML
        result = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
        
        if not pdf.err:
            # Configurar respuesta HTTP con PDF
            filename = f"Balance_Financiero_{equipo.nombre}_{timezone.now().strftime('%Y%m%d')}.pdf"
            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response
        
        self.message_user(request, "Error al generar el PDF del balance financiero", level='ERROR')
        return None
    
    descargar_balance_financiero_pdf.short_description = "Descargar balance financiero en PDF"


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cedula', 'equipo','suspendido', 'activo_segunda_fase')
    list_filter = ('equipo__categoria', 'equipo', 'equipo__torneo', 'suspendido', 'activo_segunda_fase')
    search_fields = ('primer_nombre', 'primer_apellido', 'cedula')
    ordering = ('primer_apellido',)
    list_per_page = 25
    list_select_related = ('equipo',)  # Optimización para evitar N+1 queries
    list_editable = ('cedula', 'suspendido', 'activo_segunda_fase')
    inlines = [JugadorDocumentoInline]

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
        ('Segunda fase', {
            'fields': ('activo_segunda_fase',),
            'description': 'Control para segunda fase (gestión manual)'
        }),
    )
    
    # La validación ha sido desactivada a petición del usuario
    # para permitir equipos con más de 12 jugadores activos


@admin.register(JugadorDocumento)
class JugadorDocumentoAdmin(admin.ModelAdmin):
    """Administración de documentos de jugadores con soporte para Cloudinary"""
    list_display = ('jugador', 'tipo_documento', 'estado_verificacion', 'fecha_subida', 'fecha_verificacion', 'mostrar_imagen')
    list_filter = ('tipo_documento', 'estado_verificacion', 'fecha_subida', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido', 'jugador__cedula')
    date_hierarchy = 'fecha_subida'
    ordering = ('-fecha_subida',)
    list_per_page = 25
    list_select_related = ('jugador', 'jugador__equipo')
    actions = ['marcar_como_verificados', 'marcar_como_rechazados']
    
    fieldsets = (
        ('Información del documento', {
            'fields': ('jugador', 'tipo_documento', 'archivo_documento')
        }),
        ('Estado de verificación', {
            'fields': ('estado_verificacion', 'fecha_verificacion')
        }),
        ('Metadatos', {
            'fields': ('fecha_subida', 'verificado_por'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('fecha_subida',)
    
    def mostrar_imagen(self, obj):
        """Muestra una miniatura de la imagen del documento"""
        if obj.archivo_documento:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="50" height="50" style="object-fit: cover;" /></a>',
                obj.url_documento,
                obj.url_documento
            )
        return "Sin imagen"
    mostrar_imagen.short_description = "Vista previa"
    
    def marcar_como_verificados(self, request, queryset):
        """Marca los documentos seleccionados como verificados"""
        documentos_actualizados = 0
        for documento in queryset:
            if documento.estado_verificacion != JugadorDocumento.EstadoVerificacion.VERIFICADO:
                documento.marcar_como_verificado(request.user)
                documentos_actualizados += 1
        
        self.message_user(
            request,
            f"{documentos_actualizados} documento(s) han sido marcados como verificados."
        )
    marcar_como_verificados.short_description = "Marcar documentos como verificados"
    
    def marcar_como_rechazados(self, request, queryset):
        """Marca los documentos seleccionados como rechazados"""
        documentos_actualizados = 0
        for documento in queryset:
            if documento.estado_verificacion != JugadorDocumento.EstadoVerificacion.RECHAZADO:
                documento.rechazar_documento(
                    request.user, 
                    "Documento rechazado desde el panel de administración"
                )
                documentos_actualizados += 1
        
        self.message_user(
            request,
            f"{documentos_actualizados} documento(s) han sido marcados como rechazados."
        )
    marcar_como_rechazados.short_description = "Marcar documentos como rechazados"
    
    def get_queryset(self, request):
        """Optimizar consultas para mejor rendimiento"""
        return super().get_queryset(request).select_related(
            'jugador', 'jugador__equipo', 'verificado_por'
        )