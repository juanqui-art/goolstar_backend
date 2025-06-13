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
from django.db import transaction
from cloudinary.models import CloudinaryField

from .base import Categoria, Torneo, Nivel
from ..validators import validate_document_file


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

    class Estado(models.TextChoices):
        """Estado de participación del equipo en el torneo"""
        ACTIVO = 'activo', _('Activo')
        RETIRADO = 'retirado', _('Retirado')
        SUSPENDIDO = 'suspendido', _('Suspendido')

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
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.ACTIVO)
    fecha_retiro = models.DateTimeField(null=True, blank=True)

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
        total_inscripcion = self.get_total_inscripcion()
        abonos = TransaccionPago.objects.filter(equipo=self, tipo='abono_inscripcion').aggregate(total=Sum('monto'))['total'] or 0
        return total_inscripcion - abonos

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
        from decimal import Decimal

        # Verificar si la categoría existe
        if not self.categoria:
            return Decimal('0.00')

        # Verificar si las multas están definidas en la categoría
        multa_amarilla = getattr(self.categoria, 'multa_amarilla', Decimal('0.00'))
        multa_roja = getattr(self.categoria, 'multa_roja', Decimal('0.00'))

        # Contar tarjetas no pagadas
        amarillas = Tarjeta.objects.filter(
            jugador__equipo=self, tipo='AMARILLA', pagada=False).count()
        rojas = Tarjeta.objects.filter(
            jugador__equipo=self, tipo='ROJA', pagada=False).count()

        return (amarillas * multa_amarilla) + (rojas * multa_roja)

    def get_tarjetas_no_pagadas(self, tipo=None):
        """Obtiene tarjetas no pagadas del equipo"""
        from .competicion import Tarjeta
        query = Tarjeta.objects.filter(jugador__equipo=self, pagada=False)

        if tipo:
            query = query.filter(tipo=tipo)

        return query

    def registrar_abono(self, monto, concepto="Abono a inscripción",
                        observaciones="", metodo_pago="efectivo", fecha_real=None):
        from .financiero import TransaccionPago, TipoTransaccion, MetodoPago

        if monto <= 0:
            raise ValueError("El monto debe ser mayor que cero")

        # Asegurarse que fecha_real tenga zona horaria si se proporciona
        if fecha_real and timezone.is_naive(fecha_real):
            fecha_real = timezone.make_aware(fecha_real)

        with transaction.atomic():
            transaccion = TransaccionPago.objects.create(
                equipo=self,
                tipo=TipoTransaccion.ABONO_INSCRIPCION,
                monto=monto,
                es_ingreso=True,
                concepto=concepto,
                observaciones=observaciones,
                metodo_pago=metodo_pago,
                fecha_real_transaccion=fecha_real
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
    cedula = models.CharField(max_length=20, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')
    numero_dorsal = models.PositiveSmallIntegerField(blank=True, null=True)
    posicion = models.CharField(max_length=50, blank=True, null=True)
    nivel = models.IntegerField(choices=Nivel.choices, default=Nivel.MEDIO, null=True, blank=True)
    foto = models.ImageField(upload_to='fotos_jugadores/', blank=True, null=True)

    # Campo para control de segunda fase
    activo_segunda_fase = models.BooleanField(default=True)

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
        constraints = [
            models.UniqueConstraint(
                fields=['cedula', 'equipo'],
                name='unique_cedula_equipo',
                condition=models.Q(cedula__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['equipo', 'numero_dorsal'],
                name='unique_equipo_dorsal',
                condition=models.Q(numero_dorsal__isnull=False)
            )
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


class JugadorDocumento(models.Model):
    """
    Modelo para almacenar documentos de identidad de jugadores (DNI, cédula).
    Utiliza Cloudinary para almacenamiento seguro en la nube.
    """
    
    # Tipos de documentos permitidos
    class TipoDocumento(models.TextChoices):
        DNI_FRONTAL = 'dni_frontal', 'DNI - Frontal'
        DNI_POSTERIOR = 'dni_posterior', 'DNI - Posterior' 
        CEDULA_FRONTAL = 'cedula_frontal', 'Cédula - Frontal'
        CEDULA_POSTERIOR = 'cedula_posterior', 'Cédula - Posterior'
        PASAPORTE = 'pasaporte', 'Pasaporte'
        OTRO = 'otro', 'Otro documento'
    
    # Estados de verificación
    class EstadoVerificacion(models.TextChoices):
        PENDIENTE = 'pendiente', 'Pendiente'
        VERIFICADO = 'verificado', 'Verificado'
        RECHAZADO = 'rechazado', 'Rechazado'
        RESUBIR = 'resubir', 'Requiere resubir'
    
    # Relación con jugador
    jugador = models.ForeignKey(
        Jugador, 
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Jugador'
    )
    
    # Tipo de documento
    tipo_documento = models.CharField(
        max_length=20,
        choices=TipoDocumento.choices,
        verbose_name='Tipo de documento'
    )
    
    # Archivo del documento usando Cloudinary
    archivo_documento = CloudinaryField(
        folder='goolstar_documentos',
        resource_type='auto',
        validators=[validate_document_file],
        verbose_name='Archivo del documento',
        help_text='Formatos permitidos: JPG, PNG, PDF. Tamaño máximo: 5MB'
    )
    
    # Estado de verificación
    estado_verificacion = models.CharField(
        max_length=15,
        choices=EstadoVerificacion.choices,
        default=EstadoVerificacion.PENDIENTE,
        verbose_name='Estado de verificación'
    )
    
    # Metadatos de verificación
    verificado_por = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documentos_verificados',
        verbose_name='Verificado por'
    )
    
    fecha_verificacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de verificación'
    )
    
    comentarios_verificacion = models.TextField(
        blank=True,
        verbose_name='Comentarios de verificación',
        help_text='Comentarios sobre la verificación o razones de rechazo'
    )
    
    # Timestamps
    fecha_subida = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de subida'
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Última actualización'
    )
    
    # Metadata del archivo
    tamaño_archivo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tamaño del archivo (bytes)'
    )
    
    formato_archivo = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='Formato del archivo'
    )
    
    def __str__(self):
        return f"{self.jugador.nombre_completo} - {self.get_tipo_documento_display()}"
    
    @property
    def tamaño_archivo_mb(self):
        """Retorna el tamaño del archivo en MB."""
        if self.tamaño_archivo:
            return round(self.tamaño_archivo / (1024 * 1024), 2)
        return None
    
    @property
    def url_documento(self):
        """Retorna la URL segura del documento en Cloudinary."""
        if self.archivo_documento:
            return self.archivo_documento.url
        return None
    
    @property
    def esta_verificado(self):
        """Verifica si el documento está verificado."""
        return self.estado_verificacion == self.EstadoVerificacion.VERIFICADO
    
    def marcar_como_verificado(self, usuario, comentarios=''):
        """
        Marca el documento como verificado.
        
        Args:
            usuario: Usuario que verifica el documento
            comentarios: Comentarios opcionales sobre la verificación
        """
        from django.utils import timezone
        
        self.estado_verificacion = self.EstadoVerificacion.VERIFICADO
        self.verificado_por = usuario
        self.fecha_verificacion = timezone.now()
        self.comentarios_verificacion = comentarios
        self.save()
    
    def rechazar_documento(self, usuario, comentarios):
        """
        Rechaza el documento con comentarios.
        
        Args:
            usuario: Usuario que rechaza el documento
            comentarios: Razón del rechazo (obligatorio)
        """
        from django.utils import timezone
        
        self.estado_verificacion = self.EstadoVerificacion.RECHAZADO
        self.verificado_por = usuario
        self.fecha_verificacion = timezone.now()
        self.comentarios_verificacion = comentarios
        self.save()
    
    def save(self, *args, **kwargs):
        """Override save para extraer metadata del archivo."""
        if self.archivo_documento and hasattr(self.archivo_documento, 'file'):
            # Extraer información del archivo
            if hasattr(self.archivo_documento.file, 'size'):
                self.tamaño_archivo = self.archivo_documento.file.size
            
            # Extraer formato del archivo
            if hasattr(self.archivo_documento.file, 'name'):
                import os
                _, ext = os.path.splitext(self.archivo_documento.file.name)
                self.formato_archivo = ext.lower().replace('.', '')
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Documento de Jugador"
        verbose_name_plural = "Documentos de Jugadores"
        
        # Constraint para evitar documentos duplicados del mismo tipo
        constraints = [
            models.UniqueConstraint(
                fields=['jugador', 'tipo_documento'],
                name='unique_jugador_tipo_documento',
                condition=models.Q(estado_verificacion__in=['pendiente', 'verificado'])
            )
        ]
        
        # Índices para mejorar rendimiento
        indexes = [
            models.Index(fields=['jugador', 'estado_verificacion']),
            models.Index(fields=['fecha_subida']),
            models.Index(fields=['tipo_documento']),
        ]
        
        # Ordenamiento por defecto
        ordering = ['-fecha_subida']
