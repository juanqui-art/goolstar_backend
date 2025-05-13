"""
Modelos de participantes para el sistema GoolStar.
Incluye equipos, jugadores, dirigentes y árbitros.
"""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal

from .base import Categoria, Torneo, Nivel


class Dirigente(models.Model):
    """Dirigentes de equipos"""
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Dirigente"
        verbose_name_plural = "Dirigentes"


class Equipo(models.Model):
    """Equipos participantes en el torneo"""
    
    class Grupo(models.TextChoices):
        """Grupos para la fase de grupos del torneo"""
        GRUPO_A = 'A', _('Grupo A')
        GRUPO_B = 'B', _('Grupo B')
        GRUPO_C = 'C', _('Grupo C')
        GRUPO_D = 'D', _('Grupo D')

    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='equipos')
    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='equipos')
    dirigente = models.ForeignKey(Dirigente, on_delete=models.SET_NULL, null=True, blank=True, related_name='equipos')
    logo = models.ImageField(upload_to='logos_equipos/', blank=True, null=True)
    color_principal = models.CharField(max_length=20, blank=True)
    color_secundario = models.CharField(max_length=20, blank=True)
    nivel = models.IntegerField(choices=Nivel.choices, default=Nivel.MEDIO)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    # Campos para fase de grupos
    grupo = models.CharField(max_length=1, choices=Grupo.choices, blank=True)
    
    # Campos para control de inasistencias
    inasistencias = models.PositiveSmallIntegerField(default=0)
    excluido_por_inasistencias = models.BooleanField(default=False)
    
    # Campos para eliminación directa
    clasificado_fase_grupos = models.BooleanField(default=False)
    fase_actual = models.CharField(max_length=20, blank=True)
    eliminado_en_fase = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return self.nombre
    
    @property
    def deuda_total(self):
        """Calcula la deuda total del equipo usando transacciones"""
        from .financiero import TransaccionPago
        return self.get_total_inscripcion() - TransaccionPago.objects.filter(
            equipo=self, tipo='abono_inscripcion').aggregate(total=Sum('monto'))['total'] or 0
    
    @property
    def calcular_saldo_total(self):
        """Calcula el saldo total del equipo (positivo = a favor, negativo = debe)"""
        from .financiero import TransaccionPago
        return TransaccionPago.objects.filter(equipo=self).aggregate(
            saldo=Sum('monto', filter=models.Q(es_ingreso=True)) - Sum('monto', filter=models.Q(es_ingreso=False))
        )['saldo'] or Decimal('0.00')
    
    def calcular_saldo_para_acta(self, hasta_partido=None):
        """Calcula el saldo anterior para mostrar en el acta de un partido específico"""
        from .financiero import TransaccionPago
        query = TransaccionPago.objects.filter(equipo=self)
        
        if hasta_partido:
            query = query.filter(fecha__lt=hasta_partido.fecha)
            
        return query.aggregate(
            saldo=Sum('monto', filter=models.Q(es_ingreso=True)) - Sum('monto', filter=models.Q(es_ingreso=False))
        )['saldo'] or Decimal('0.00')
    
    def get_total_inscripcion(self):
        """Calcula el total de inscripción incluyendo multas pendientes"""
        costo_base = self.categoria.costo_inscripcion or Decimal('0.00')
        multas_pendientes = self.get_deuda_multas_pendientes()
        return costo_base + multas_pendientes
    
    def get_deuda_multas_pendientes(self):
        """Calcula deuda por multas de tarjetas pendientes de pago"""
        from .competicion import Tarjeta
        amarillas = Tarjeta.objects.filter(
            jugador__equipo=self, tipo='AMARILLA', pagada=False).count()
        rojas = Tarjeta.objects.filter(
            jugador__equipo=self, tipo='ROJA', pagada=False).count()
        
        return (amarillas * self.categoria.multa_amarilla) + (rojas * self.categoria.multa_roja)
    
    def get_tarjetas_no_pagadas(self, tipo=None):
        """Obtiene tarjetas no pagadas del equipo"""
        from .competicion import Tarjeta
        query = Tarjeta.objects.filter(jugador__equipo=self, pagada=False)
        
        if tipo:
            query = query.filter(tipo=tipo)
            
        return query
    
    def registrar_abono(self, monto, concepto="Abono a inscripción", observaciones=""):
        """Registra un abono del equipo"""
        from .financiero import TransaccionPago, TipoTransaccion
        
        # Validar que el monto sea positivo
        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")
        
        # Crear la transacción de pago
        transaccion = TransaccionPago.objects.create(
            equipo=self,
            tipo=TipoTransaccion.ABONO_INSCRIPCION,
            monto=monto,
            es_ingreso=True,
            concepto=concepto,
            observaciones=observaciones
        )
        
        return transaccion
    
    def verificar_suspension_por_inasistencias(self):
        """Verifica si el equipo debe ser excluido por inasistencias"""
        if self.inasistencias >= self.categoria.limite_inasistencias and not self.excluido_por_inasistencias:
            self.excluido_por_inasistencias = True
            self.activo = False
            self.save()
            return True
        return False
    
    def clasificar_a_eliminacion(self):
        """Marca el equipo como clasificado a eliminación directa"""
        self.clasificado_fase_grupos = True
        self.fase_actual = 'eliminatorias'
        self.save()
    
    def eliminar_en_fase(self, fase):
        """Marca el equipo como eliminado en una fase específica"""
        self.eliminado_en_fase = fase
        self.fase_actual = ''
        self.save()
    
    def get_historial_pagos(self):
        """Obtiene el historial completo de pagos del equipo"""
        from .financiero import TransaccionPago
        return TransaccionPago.objects.filter(equipo=self).order_by('-fecha')
    
    def get_balance_por_tipo(self):
        """Obtiene el balance desglosado por tipo de transacción"""
        from .financiero import TransaccionPago
        return TransaccionPago.objects.filter(equipo=self).values('tipo').annotate(
            total=Sum('monto', filter=models.Q(es_ingreso=True)) - Sum('monto', filter=models.Q(es_ingreso=False))
        )
    
    class Meta:
        unique_together = ['nombre', 'categoria', 'torneo']
        verbose_name = "Equipo"
        verbose_name_plural = "Equipos"


class Jugador(models.Model):
    """Jugadores registrados en cada equipo"""
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100, blank=True, null=True)
    cedula = models.CharField(max_length=20)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')
    numero_dorsal = models.PositiveSmallIntegerField()
    posicion = models.CharField(max_length=50, blank=True)
    nivel = models.IntegerField(choices=Nivel.choices, default=Nivel.MEDIO)
    foto = models.ImageField(upload_to='fotos_jugadores/', blank=True, null=True)
    
    # Campos para control de suspensiones
    suspendido = models.BooleanField(default=False)
    partidos_suspension_restantes = models.PositiveSmallIntegerField(default=0)
    fecha_fin_suspension = models.DateField(blank=True, null=True)

    def __str__(self):
        if self.segundo_apellido:
            return f"{self.primer_apellido} {self.segundo_apellido} {self.primer_nombre}"
        return f"{self.primer_apellido} {self.primer_nombre}"
    
    @property
    def nombre_completo(self):
        nombres = f"{self.primer_nombre}"
        if self.segundo_nombre:
            nombres += f" {self.segundo_nombre}"
        return f"{nombres} {self.primer_apellido} {self.segundo_apellido or ''}".strip()
    
    def get_amarillas_acumuladas(self):
        """Cuenta amarillas acumuladas sin suspensión cumplida"""
        from .competicion import Tarjeta
        return Tarjeta.objects.filter(jugador=self, tipo='AMARILLA', suspension_cumplida=False).count()
    
    def verificar_suspension_por_amarillas(self):
        """Verifica si el jugador debe ser suspendido por amarillas"""
        from .competicion import Tarjeta
        amarillas = self.get_amarillas_acumuladas()
        limite = self.equipo.categoria.limite_amarillas_suspension
        
        if amarillas >= limite:
            # Marcar al jugador como suspendido
            self.suspendido = True
            self.partidos_suspension_restantes = 1
            self.save()
            
            # Marcar las tarjetas como procesadas para suspensión
            Tarjeta.objects.filter(
                jugador=self, 
                tipo='AMARILLA', 
                suspension_cumplida=False
            ).update(suspension_cumplida=True)
            
            return True
        return False
    
    @property
    def puede_jugar(self):
        """Verifica si el jugador puede participar (no suspendido)"""
        return not self.suspendido
    
    class Meta:
        unique_together = [
            ['cedula', 'equipo'],
            ['equipo', 'numero_dorsal']
        ]
        verbose_name = "Jugador"
        verbose_name_plural = "Jugadores"


class Arbitro(models.Model):
    """Árbitros del torneo"""
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    # Campos específicos para árbitros
    experiencia_anos = models.PositiveSmallIntegerField(blank=True, null=True)
    categoria_maxima = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def partidos_arbitrados(self):
        from .competicion import Partido
        return Partido.objects.filter(arbitro=self).count()
    
    @property
    def total_cobrado(self):
        from .financiero import PagoArbitro
        return PagoArbitro.objects.filter(arbitro=self, pagado=True).aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
    
    @property
    def total_por_cobrar(self):
        from .financiero import PagoArbitro
        return PagoArbitro.objects.filter(arbitro=self, pagado=False).aggregate(
            total=Sum('monto'))['total'] or Decimal('0.00')
    
    class Meta:
        verbose_name = "Árbitro"
        verbose_name_plural = "Árbitros"
