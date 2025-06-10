"""
Modelos financieros para el sistema GoolStar.
Incluye transacciones de pago y pagos a árbitros.
"""

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal

from .participantes import Equipo, Arbitro


class TipoTransaccion(models.TextChoices):
    """Tipos de transacciones de pago"""
    ABONO_INSCRIPCION = 'abono_inscripcion', _('Abono a Inscripción')
    PAGO_ARBITRO = 'pago_arbitro', _('Pago de Árbitro')
    PAGO_BALON = 'pago_balon', _('Pago de Balón')
    MULTA_AMARILLA = 'multa_amarilla', _('Multa por Tarjeta Amarilla')
    MULTA_ROJA = 'multa_roja', _('Multa por Tarjeta Roja')
    AJUSTE_MANUAL = 'ajuste_manual', _('Ajuste Manual')
    DEVOLUCION = 'devolucion', _('Devolución')


# En api/models/financiero.py - Añadir primero el enum
class MetodoPago(models.TextChoices):
    EFECTIVO = 'efectivo', _('Efectivo')
    TRANSFERENCIA = 'transferencia', _('Transferencia Bancaria')
    DEPOSITO = 'deposito', _('Depósito Bancario')
    TARJETA = 'tarjeta', _('Tarjeta de Crédito/Débito')
    OTRO = 'otro', _('Otro')


# En la clase TransaccionPago, añadir el campo


class TransaccionPago(models.Model):
    """Registro detallado de todas las transacciones de pago de los equipos"""
    equipo = models.ForeignKey(Equipo, on_delete=models.PROTECT, related_name='transacciones')
    partido = models.ForeignKey('api.Partido', on_delete=models.SET_NULL, related_name='transacciones_pago', blank=True,
                                null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(max_length=20, choices=TipoTransaccion.choices)
    monto = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    es_ingreso = models.BooleanField(default=False,
                                     help_text="True si es un ingreso para el torneo, False si es un gasto")
    concepto = models.CharField(max_length=100)
    metodo_pago = models.CharField(
        max_length=20,
        choices=MetodoPago.choices,
        default=MetodoPago.EFECTIVO,
        blank=True
    )
    fecha_real_transaccion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha real de la transacción"
    )
    # En TransaccionPago, añadir el campo
    referencia_pago = models.CharField(
        max_length=100,
        blank=True,
        help_text="Número de referencia de transferencia, recibo, etc."
    )
    # Campos para transacciones específicas
    tarjeta = models.ForeignKey('api.Tarjeta', on_delete=models.SET_NULL, blank=True, null=True)
    jugador = models.ForeignKey('api.Jugador', on_delete=models.SET_NULL, blank=True, null=True)

    # Información adicional
    observaciones = models.TextField(blank=True)
    creado_automaticamente = models.BooleanField(default=False)

    def clean(self):
        if self.tipo == 'multa_amarilla' or self.tipo == 'multa_roja':
            if not self.tarjeta:
                raise ValidationError("Para multas por tarjetas se debe especificar la tarjeta")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    @property
    def es_gasto(self):
        """Indica si la transacción es un gasto"""
        return self.tipo in ['pago_arbitro', 'pago_balon', 'devolucion']

    def __str__(self):
        return f"{self.equipo.nombre} - {self.get_tipo_display()} - ${self.monto}"

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Transacción de Pago"
        verbose_name_plural = "Transacciones de Pago"


class PagoArbitro(models.Model):
    """Pagos realizados a árbitros por equipos"""
    arbitro = models.ForeignKey(Arbitro, on_delete=models.CASCADE, related_name='pagos')
    partido = models.ForeignKey('api.Partido', on_delete=models.CASCADE, related_name='pagos_arbitro')
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='pagos_arbitro')
    monto = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(Decimal('0'))])
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(blank=True, null=True)
    metodo_pago = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"Pago a {self.arbitro} por {self.equipo.nombre} - {self.partido}"

    def save(self, *args, **kwargs):
        # Si se marca como pagado y no tiene fecha de pago, establecer la fecha actual
        if self.pagado and not self.fecha_pago:
            self.fecha_pago = timezone.now()

        # Actualizar el estado de pago en el partido
        if self.pagado:
            if self.equipo == self.partido.equipo_1:
                self.partido.equipo_1_pago_arbitro = True
            elif self.equipo == self.partido.equipo_2:
                self.partido.equipo_2_pago_arbitro = True
            self.partido.save()

        super().save(*args, **kwargs)

    class Meta:
        unique_together = ['arbitro', 'partido', 'equipo']
        verbose_name = "Pago a Árbitro"
        verbose_name_plural = "Pagos a Árbitros"
