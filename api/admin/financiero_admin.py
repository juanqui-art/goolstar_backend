"""
Configuraciones de administración para modelos financieros.
Incluye administración de Transacciones de Pago y Pagos de Árbitros.
"""

from django.contrib import admin

# Importaciones de modelos financieros
from ..models.financiero import TransaccionPago, PagoArbitro


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

    def marcar_como_pagados(self, _, queryset):
        from django.utils import timezone
        queryset.update(pagado=True, fecha_pago=timezone.now())

    marcar_como_pagados.short_description = "Marcar pagos seleccionados como pagados"