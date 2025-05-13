from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Nivel(models.IntegerChoices):
    """Niveles de habilidad para jugadores y equipos"""
    MUY_BAJO = 1, _('1 - Muy bajo')
    BAJO = 2, _('2 - Bajo')
    MEDIO = 3, _('3 - Medio')
    ALTO = 4, _('4 - Alto')
    MUY_ALTO = 5, _('5 - Muy alto')


class Categoria(models.Model):
    """Categorías del torneo: VARONES, DAMAS, MÁSTER"""

    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    premio_primero = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                         validators=[MinValueValidator(0)])
    premio_segundo = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                         validators=[MinValueValidator(0)])
    premio_tercero = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                         validators=[MinValueValidator(0)])
    premio_cuarto = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                        validators=[MinValueValidator(0)])
    costo_inscripcion = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                            validators=[MinValueValidator(0)])
    # Campos para configuración del torneo
    costo_arbitraje = models.DecimalField(max_digits=6, decimal_places=2, default=10.00,
                                          validators=[MinValueValidator(0)])
    multa_amarilla = models.DecimalField(max_digits=6, decimal_places=2, default=2.00,
                                         validators=[MinValueValidator(0)])
    multa_roja = models.DecimalField(max_digits=6, decimal_places=2, default=3.00, validators=[MinValueValidator(0)])
    limite_inasistencias = models.PositiveSmallIntegerField(default=3)
    limite_amarillas_suspension = models.PositiveSmallIntegerField(default=3)
    partidos_suspension_roja = models.PositiveSmallIntegerField(default=2)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"


class Torneo(models.Model):
    """Configuración y control de torneos"""

    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='torneos')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    finalizado = models.BooleanField(default=False)
    # Configuración del formato
    tiene_fase_grupos = models.BooleanField(default=True)
    tiene_eliminacion_directa = models.BooleanField(default=True)
    numero_grupos = models.PositiveSmallIntegerField(default=2)
    equipos_clasifican_por_grupo = models.PositiveSmallIntegerField(default=2)

    # Estado actual del torneo
    fase_actual = models.CharField(max_length=20, choices=[
        ('inscripcion', 'Inscripción'),
        ('grupos', 'Fase de Grupos'),
        ('octavos', 'Octavos de Final'),
        ('cuartos', 'Cuartos de Final'),
        ('semifinales', 'Semifinales'),
        ('final', 'Final'),
        ('finalizado', 'Finalizado'),
    ], default='inscripcion')

    def __str__(self):
        return f"{self.nombre} - {self.categoria.nombre}"

    @property
    def equipos_participantes(self):
        return self.equipos.filter(activo=True)

    @property
    def puede_iniciar_eliminacion(self):
        """Verifica si se puede iniciar la fase de eliminación directa"""
        if not self.tiene_eliminacion_directa or self.fase_actual != 'grupos':
            return False

        grupos_completos = all(
            self.equipos_en_grupo(grupo).count() > 0
            for grupo in ['A', 'B'][:self.numero_grupos]
        )
        return grupos_completos

    def equipos_en_grupo(self, grupo):
        """Retorna equipos de un grupo específico"""
        return self.equipos.filter(grupo=grupo, activo=True)

    def obtener_clasificados(self):
        """Obtiene los equipos clasificados de la fase de grupos"""
        clasificados = []

        for grupo in ['A', 'B'][:self.numero_grupos]:
            equipos_grupo = self.equipos_en_grupo(grupo)
            clasificados.extend(equipos_grupo[:self.equipos_clasifican_por_grupo])

        return clasificados

    class Meta:
        verbose_name = "Torneo"
        verbose_name_plural = "Torneos"


class FaseEliminatoria(models.Model):
    """Fases de eliminación directa del torneo"""

    torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='fases_eliminatorias')
    nombre = models.CharField(max_length=50)
    orden = models.PositiveSmallIntegerField()
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.torneo.nombre} - {self.nombre}"

    @property
    def partidos_pendientes(self):
        return self.partidos.filter(jugado=False).count()

    @property
    def puede_iniciar_siguiente_fase(self):
        return self.completada and self.partidos_pendientes == 0

    class Meta:
        unique_together = ['torneo', 'orden']
        ordering = ['orden']
        verbose_name = "Fase Eliminatoria"
        verbose_name_plural = "Fases Eliminatorias"


class Dirigente(models.Model):
    """Dirigentes de equipos"""

    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre} - {self.telefono}"

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
    dirigente = models.OneToOneField(Dirigente, on_delete=models.CASCADE, related_name='equipo')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    pago_completo = models.BooleanField(default=False)
    abono = models.DecimalField(max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    telefono_contacto = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='logos_equipos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    grupo = models.CharField(max_length=1, choices=Grupo.choices, blank=True, null=True)
    nivel = models.PositiveSmallIntegerField(choices=Nivel.choices, blank=True, null=True, verbose_name='Nivel')

    # Campos para tracking de deudas e inasistencias
    inasistencias = models.PositiveSmallIntegerField(default=0)
    excluido = models.BooleanField(default=False)
    fecha_exclusion = models.DateTimeField(blank=True, null=True)
    motivo_exclusion = models.TextField(blank=True)

    # Campos para eliminación directa
    clasificado_fase_grupos = models.BooleanField(default=False)
    fase_actual = models.CharField(max_length=20, blank=True)
    eliminado_en_fase = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"

    @property
    def deuda_total(self):
        """Calcula la deuda total del equipo usando transacciones"""
        return self.calcular_saldo_total()

    def calcular_saldo_total(self):
        """Calcula el saldo total del equipo (positivo = a favor, negativo = debe)"""
        total = self.transacciones.aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        return total

    def calcular_saldo_para_acta(self, hasta_partido=None):
        """Calcula el saldo anterior para mostrar en el acta de un partido específico"""
        query = self.transacciones.all()
        if hasta_partido:
            query = query.exclude(partido=hasta_partido)

        total = query.aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        return total

    def get_total_inscripcion(self):
        """Calcula el total de inscripción incluyendo multas pendientes"""
        inscripcion_base = self.categoria.costo_inscripcion or Decimal('0')
        multas_pendientes = self.get_deuda_multas_pendientes()
        return inscripcion_base + multas_pendientes

    def get_deuda_multas_pendientes(self):
        """Calcula deuda por multas de tarjetas pendientes de pago"""
        total_multas = self.transacciones.filter(
            tipo__in=['multa_amarilla', 'multa_roja'],
            monto__lt=0
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')

        return abs(total_multas)

    def get_tarjetas_no_pagadas(self, tipo=None):
        """Obtiene tarjetas no pagadas del equipo"""
        tarjetas = Tarjeta.objects.filter(
            jugador__equipo=self,
            multa_pagada=False
        )
        if tipo:
            tarjetas = tarjetas.filter(tipo=tipo)
        return tarjetas

    def registrar_abono(self, monto, concepto="Abono a inscripción", observaciones=""):
        """Registra un abono del equipo"""
        transaccion = TransaccionPago.objects.create(
            equipo=self,
            tipo=TipoTransaccion.ABONO_INSCRIPCION,
            concepto=concepto,
            monto=monto,
            observaciones=observaciones,
            creado_automaticamente=False
        )

        self.abono = self.transacciones.filter(
            tipo=TipoTransaccion.ABONO_INSCRIPCION
        ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0')
        self.save()

        return transaccion

    def verificar_suspension_por_inasistencias(self):
        """Verifica si el equipo debe ser excluido por inasistencias"""
        if self.inasistencias >= self.categoria.limite_inasistencias and not self.excluido:
            self.excluido = True
            self.fecha_exclusion = timezone.now()
            self.motivo_exclusion = f"Excluido por {self.inasistencias} inasistencias"
            self.save()
            return True
        return False

    def clasificar_a_eliminacion(self):
        """Marca el equipo como clasificado a eliminación directa"""
        self.clasificado_fase_grupos = True
        self.fase_actual = 'octavos'
        self.save()

    def eliminar_en_fase(self, fase):
        """Marca el equipo como eliminado en una fase específica"""
        self.eliminado_en_fase = fase
        self.activo = False
        self.save()

    def get_historial_pagos(self):
        """Obtiene el historial completo de pagos del equipo"""
        return self.transacciones.all().order_by('-fecha')

    def get_balance_por_tipo(self):
        """Obtiene el balance desglosado por tipo de transacción"""
        return self.transacciones.values('tipo').annotate(
            total=models.Sum('monto'),
            cantidad=models.Count('id')
        ).order_by('tipo')

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
    cedula = models.CharField(max_length=15)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')
    numero_dorsal = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Número de Dorsal')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    nivel = models.PositiveSmallIntegerField(choices=Nivel.choices, blank=True, null=True, verbose_name='Nivel')
    cedula_imagen = models.ImageField(upload_to='cedulas_jugadores/', blank=True, null=True,
                                      verbose_name='Imagen de la cédula')
    # Campos para control de suspensiones
    suspendido = models.BooleanField(default=False)
    partidos_suspension_restantes = models.PositiveSmallIntegerField(default=0)
    fecha_fin_suspension = models.DateField(blank=True, null=True)

    def __str__(self):
        nombres = f"{self.primer_nombre} {self.segundo_nombre or ''}".strip()
        apellidos = f"{self.primer_apellido} {self.segundo_apellido or ''}".strip()
        dorsal = f" #{self.numero_dorsal}" if self.numero_dorsal else ""
        return f"{nombres} {apellidos}{dorsal}".strip()

    @property
    def nombre_completo(self):
        return str(self)

    def get_amarillas_acumuladas(self):
        """Cuenta amarillas acumuladas sin suspensión cumplida"""
        return self.tarjetas.filter(tipo='AMARILLA', suspension_cumplida=False).count()

    def verificar_suspension_por_amarillas(self):
        """Verifica si el jugador debe ser suspendido por amarillas"""
        amarillas = self.get_amarillas_acumuladas()
        limite = self.equipo.categoria.limite_amarillas_suspension

        if amarillas >= limite and not self.suspendido:
            self.suspendido = True
            self.partidos_suspension_restantes = 1
            self.tarjetas.filter(tipo='AMARILLA', suspension_cumplida=False).update(suspension_cumplida=True)
            self.save()
            return True
        return False

    def puede_jugar(self):
        """Verifica si el jugador puede participar (no suspendido)"""
        return not self.suspendido and self.partidos_suspension_restantes == 0

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
        return f"{self.nombres} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def partidos_arbitrados(self):
        return self.partidos.count()

    @property
    def total_cobrado(self):
        return self.pagos.filter(pagado=True).aggregate(
            total=models.Sum('monto'))['total'] or Decimal('0')

    @property
    def total_por_cobrar(self):
        return self.pagos.filter(pagado=False).aggregate(
            total=models.Sum('monto'))['total'] or Decimal('0')

    class Meta:
        verbose_name = "Árbitro"
        verbose_name_plural = "Árbitros"


class Jornada(models.Model):
    """Jornadas del torneo"""


nombre = models.CharField(max_length=50, unique=True)
numero = models.PositiveIntegerField()
fecha = models.DateField(blank=True, null=True)
activa = models.BooleanField(default=False)


def __str__(self):
    return self.nombre


class Meta:
    verbose_name = "Jornada"
    verbose_name_plural = "Jornadas"
    ordering = ['numero']


class Partido(models.Model):
    """Partidos del torneo"""


torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='partidos')
jornada = models.ForeignKey(Jornada, on_delete=models.CASCADE, related_name='partidos', blank=True, null=True)
fase_eliminatoria = models.ForeignKey(FaseEliminatoria, on_delete=models.CASCADE, related_name='partidos', blank=True,
                                      null=True)
equipo_1 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_equipo_1')
equipo_2 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_equipo_2')
arbitro = models.ForeignKey(Arbitro, on_delete=models.SET_NULL, null=True, blank=True, related_name='partidos')
fecha = models.DateTimeField()
goles_equipo_1 = models.PositiveSmallIntegerField(default=0)
goles_equipo_2 = models.PositiveSmallIntegerField(default=0)
jugado = models.BooleanField(default=False)
fecha_nombre = models.CharField(max_length=50, blank=True, null=True)
# Campos para control de arbitraje
arbitro_pagado_equipo_1 = models.BooleanField(default=False)
arbitro_pagado_equipo_2 = models.BooleanField(default=False)
costo_arbitraje = models.DecimalField(max_digits=6, decimal_places=2, default=10.00)

# Campos detallados del acta para pagos
saldo_anterior_equipo_1 = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                              verbose_name='Saldo anterior Eq. 1')
saldo_anterior_equipo_2 = models.DecimalField(max_digits=8, decimal_places=2, default=0,
                                              verbose_name='Saldo anterior Eq. 2')
balon_equipo_1 = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Balón Eq. 1')
balon_equipo_2 = models.DecimalField(max_digits=6, decimal_places=2, default=0, verbose_name='Balón Eq. 2')
total_tarjetas_equipo_1 = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                              verbose_name='Total tarjetas Eq. 1')
total_tarjetas_equipo_2 = models.DecimalField(max_digits=6, decimal_places=2, default=0,
                                              verbose_name='Total tarjetas Eq. 2')
total_inscripcion_equipo_1 = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Total Eq. 1')
total_inscripcion_equipo_2 = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Total Eq. 2')
abono_equipo_1 = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Abono Eq. 1')
abono_equipo_2 = models.DecimalField(max_digits=8, decimal_places=2, default=0, verbose_name='Abono Eq. 2')

# Campos de control del partido
equipo_1_presente = models.BooleanField(default=True)
equipo_2_presente = models.BooleanField(default=True)
motivo_suspension = models.TextField(blank=True)
observaciones_arbitro = models.TextField(blank=True)

# Campos para eliminación directa
es_eliminatorio = models.BooleanField(default=False)
equipo_ganador = models.ForeignKey('Equipo', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='partidos_ganados')
definido_por_penales = models.BooleanField(default=False)
penales_equipo_1 = models.PositiveSmallIntegerField(blank=True, null=True)
penales_equipo_2 = models.PositiveSmallIntegerField(blank=True, null=True)


def clean(self):
    super().clean()
    if self.equipo_1 == self.equipo_2:
        raise ValidationError('Los equipos no pueden ser iguales en un partido.')

    if self.jornada and self.fase_eliminatoria:
        raise ValidationError('Un partido no puede pertenecer a una jornada y una fase eliminatoria.')


def __str__(self):
    fase = ""
    if self.fase_eliminatoria:
        fase = f" ({self.fase_eliminatoria.nombre})"
    return f"{self.equipo_1} vs {self.equipo_2}{fase}"


def save(self, *args, **kwargs):
    self.full_clean()

    # Determinar el ganador automáticamente si es eliminatorio
    if self.es_eliminatorio and self.jugado:
        if self.definido_por_penales:
            if self.penales_equipo_1 > self.penales_equipo_2:
                self.equipo_ganador = self.equipo_1
            elif self.penales_equipo_2 > self.penales_equipo_1:
                self.equipo_ganador = self.equipo_2
        else:
            if self.goles_equipo_1 > self.goles_equipo_2:
                self.equipo_ganador = self.equipo_1
            elif self.goles_equipo_2 > self.goles_equipo_1:
                self.equipo_ganador = self.equipo_2

    super().save(*args, **kwargs)

    # Si es eliminatorio, actualizar el estado del equipo perdedor
    if self.es_eliminatorio and self.jugado and self.equipo_ganador:
        perdedor = self.equipo_2 if self.equipo_ganador == self.equipo_1 else self.equipo_1
        if self.fase_eliminatoria:
            perdedor.eliminar_en_fase(self.fase_eliminatoria.nombre)


# Métodos para trabajar con participaciones
def get_participaciones_equipo(self, equipo):
    """Obtiene todas las participaciones de un equipo en este partido"""
    return self.participaciones.filter(jugador__equipo=equipo).order_by('numero_dorsal')


def get_jugadores_titulares(self, equipo):
    """Obtiene jugadores titulares de un equipo"""
    return self.participaciones.filter(
        jugador__equipo=equipo,
        titular=True
    ).order_by('numero_dorsal')


def get_jugadores_salen(self, equipo):
    """Obtiene jugadores que salen durante el partido"""
    return self.participaciones.filter(
        jugador__equipo=equipo,
        minuto_salida__isnull=False
    ).order_by('numero_dorsal')


def get_cambios_realizados(self, equipo):
    """Cuenta los cambios realizados por un equipo"""
    return self.participaciones.filter(
        jugador__equipo=equipo,
        titular=False,
        minuto_entrada__gt=0
    ).count()


def validar_minimo_jugadores(self):
    """Valida que cada equipo tenga al menos 4 jugadores"""
    jugadores_eq1 = self.participaciones.filter(jugador__equipo=self.equipo_1).count()
    jugadores_eq2 = self.participaciones.filter(jugador__equipo=self.equipo_2).count()

    errores = []
    if jugadores_eq1 < 4:
        errores.append(f'{self.equipo_1.nombre} debe tener al menos 4 jugadores')
    if jugadores_eq2 < 4:
        errores.append(f'{self.equipo_2.nombre} debe tener al menos 4 jugadores')

    return errores


@property
def resultado(self):
    """Retorna el resultado del partido incluyendo penales si aplica"""
    if self.jugado:
        resultado = f"{self.goles_equipo_1} - {self.goles_equipo_2}"
        if self.definido_por_penales:
            resultado += f" ({self.penales_equipo_1} - {self.penales_equipo_2} pen.)"
        return resultado
    return "Sin jugar"


@property
def arbitro_completamente_pagado(self):
    """Verifica si ambos equipos han pagado al árbitro"""
    return self.arbitro_pagado_equipo_1 and self.arbitro_pagado_equipo_2


@property
def arbitro_asignado(self):
    """Retorna el nombre del árbitro o 'Sin asignar'"""
    return self.arbitro.nombre_completo if self.arbitro else "Sin asignar"


@property
def es_fase_grupos(self):
    """Determina si es partido de fase de grupos"""
    return self.jornada is not None and not self.es_eliminatorio


def marcar_inasistencia(self, equipo):
    """Marca inasistencia de un equipo y actualiza contador"""
    if equipo == self.equipo_1:
        self.equipo_1_presente = False
        self.goles_equipo_1 = 0
        self.goles_equipo_2 = 3
    elif equipo == self.equipo_2:
        self.equipo_2_presente = False
        self.goles_equipo_1 = 3
        self.goles_equipo_2 = 0

    self.jugado = True
    equipo.inasistencias += 1
    equipo.save()
    self.save()

    equipo.verificar_suspension_por_inasistencias()


class Meta:
    verbose_name = "Partido"
    verbose_name_plural = "Partidos"


class TipoTransaccion(models.TextChoices):
    """Tipos de transacciones de pago"""


ABONO_INSCRIPCION = 'abono_inscripcion', _('Abono a Inscripción')
PAGO_ARBITRO = 'pago_arbitro', _('Pago de Árbitro')
PAGO_BALON = 'pago_balon', _('Pago de Balón')
MULTA_AMARILLA = 'multa_amarilla', _('Multa por Tarjeta Amarilla')
MULTA_ROJA = 'multa_roja', _('Multa por Tarjeta Roja')
AJUSTE_MANUAL = 'ajuste_manual', _('Ajuste Manual')
DEVOLUCION = 'devolucion', _('Devolución')


class TransaccionPago(models.Model):
    """Registro detallado de todas las transacciones de pago de los equipos"""


equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='transacciones')
partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='transacciones_pago', blank=True, null=True)
tipo = models.CharField(max_length=30, choices=TipoTransaccion.choices)
concepto = models.CharField(max_length=200)
monto = models.DecimalField(max_digits=8, decimal_places=2)
fecha = models.DateTimeField(auto_now_add=True)
# Referencias opcionales para trazabilidad
tarjeta = models.ForeignKey('Tarjeta', on_delete=models.CASCADE, blank=True, null=True, related_name='transaccion')
jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE, blank=True, null=True)

# Información adicional
observaciones = models.TextField(blank=True)
creado_automaticamente = models.BooleanField(default=False)


def clean(self):
    super().clean()
    if self.tipo in ['multa_amarilla', 'multa_roja', 'pago_arbitro', 'pago_balon'] and self.monto > 0:
        self.monto = -abs(self.monto)


def save(self, *args, **kwargs):
    self.clean()
    super().save(*args, **kwargs)


@property
def es_ingreso(self):
    """Indica si la transacción es un ingreso"""
    return self.monto > 0


@property
def es_gasto(self):
    """Indica si la transacción es un gasto"""
    return self.monto < 0


def __str__(self):
    signo = "+" if self.es_ingreso else ""
    return f"{self.equipo.nombre} - {self.concepto} - {signo}${self.monto}"


class Meta:
    ordering = ['-fecha']
    verbose_name = "Transacción de Pago"
    verbose_name_plural = "Transacciones de Pago"


class ParticipacionJugador(models.Model):
    """Registro detallado de participación de jugadores en cada partido"""


partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='participaciones')
jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='participaciones')
numero_dorsal = models.PositiveSmallIntegerField(verbose_name='Dorsal usado en el partido')
titular = models.BooleanField(default=True, verbose_name='¿Fue titular?')
minuto_entrada = models.PositiveSmallIntegerField(default=0, verbose_name='Minuto de entrada')
minuto_salida = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Minuto de salida')
# Campos adicionales
activo = models.BooleanField(default=True, help_text='¿Está aún en el campo?')
motivo_salida = models.CharField(max_length=20, blank=True, choices=[
    ('cambio', 'Cambio técnico'),
    ('lesion', 'Lesión'),
    ('tarjeta_roja', 'Tarjeta roja'),
    ('suspension', 'Suspensión'),
])


def clean(self):
    super().clean()

    # Validar que el jugador pertenezca a uno de los equipos del partido
    if self.jugador.equipo not in [self.partido.equipo_1, self.partido.equipo_2]:
        raise ValidationError(f'{self.jugador} no pertenece a ninguno de los equipos de este partido')

    # Validar que no haya dorsales repetidos en el mismo equipo para este partido
    dorsales_usados = ParticipacionJugador.objects.filter(
        partido=self.partido,
        jugador__equipo=self.jugador.equipo,
        numero_dorsal=self.numero_dorsal
    ).exclude(pk=self.pk)

    if dorsales_usados.exists():
        raise ValidationError(
            f'El dorsal #{self.numero_dorsal} ya está siendo usado por otro jugador de {self.jugador.equipo.nombre}')

    # Validar que el jugador no esté suspendido
    if not self.jugador.puede_jugar():
        raise ValidationError(f'{self.jugador} está suspendido y no puede participar')

    # Validar minutos lógicos
    if self.minuto_salida and self.minuto_salida <= self.minuto_entrada:
        raise ValidationError('El minuto de salida debe ser mayor al minuto de entrada')


def save(self, *args, **kwargs):
    # Auto-determinar si sigue activo
    if self.minuto_salida:
        self.activo = False

    super().save(*args, **kwargs)

    # Validar el límite de cambios después de guardar
    self.validar_limite_cambios()


def validar_limite_cambios(self):
    """Valida que no se excedan los 3 cambios permitidos por equipo"""
    cambios = ParticipacionJugador.objects.filter(
        partido=self.partido,
        jugador__equipo=self.jugador.equipo,
        titular=False,
        minuto_entrada__gt=0
    ).count()

    if cambios > 3:
        raise ValidationError(f'{self.jugador.equipo.nombre} ha excedido el límite de 3 cambios permitidos')


@property
def minutos_jugados(self):
    """Calcula los minutos jugados por el jugador"""
    if not self.minuto_salida:
        return 45 - self.minuto_entrada
    return self.minuto_salida - self.minuto_entrada


@property
def salio_durante_partido(self):
    """Indica si el jugador salió antes del final del partido"""
    return self.minuto_salida is not None and self.minuto_salida < 45


def __str__(self):
    estado = "SALE" if self.salio_durante_partido else "TITULAR" if self.titular else "ENTRA"
    return f"{self.jugador} #{self.numero_dorsal} ({estado}) - {self.partido}"


class Meta:
    unique_together = [
        ['partido', 'jugador'],
        ['partido', 'jugador__equipo', 'numero_dorsal']
    ]
    verbose_name = "Participación de Jugador"
    verbose_name_plural = "Participaciones de Jugadores"
    ordering = ['jugador__equipo', 'numero_dorsal']


class PagoArbitro(models.Model):
    """Pagos realizados a árbitros por equipos"""


arbitro = models.ForeignKey(Arbitro, on_delete=models.CASCADE, related_name='pagos')
partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='pagos_arbitro')
equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='pagos_arbitro')
monto = models.DecimalField(max_digits=6, decimal_places=2, validators=[MinValueValidator(0)])
pagado = models.BooleanField(default=False)
fecha_pago = models.DateTimeField(blank=True, null=True)
metodo_pago = models.CharField(max_length=50, blank=True)


def __str__(self):
    return f"{self.equipo} - {self.arbitro} - {self.partido} - ${self.monto}"


def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    # Actualizar el estado de pago en el partido
    if self.pagado:
        if self.equipo == self.partido.equipo_1:
            self.partido.arbitro_pagado_equipo_1 = True
        elif self.equipo == self.partido.equipo_2:
            self.partido.arbitro_pagado_equipo_2 = True
        self.partido.save()


class Meta:
    unique_together = ['arbitro', 'partido', 'equipo']
    verbose_name = "Pago a Árbitro"
    verbose_name_plural = "Pagos a Árbitros"


class Gol(models.Model):
    """Goles anotados en partidos"""


jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE, related_name='goles')
partido = models.ForeignKey('Partido', on_delete=models.CASCADE, related_name='goles')
minuto = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Minuto (opcional)')
autogol = models.BooleanField(default=False)


def __str__(self):
    auto = " (autogol)" if self.autogol else ""
    return f"{self.jugador} - {self.partido}{auto}"


class Meta:
    verbose_name = "Gol"
    verbose_name_plural = "Goles"


class Tarjeta(models.Model):
    """Registro de tarjetas amarillas y rojas"""


class Tipo(models.TextChoices):
    """Tipos de tarjetas en fútbol"""
    AMARILLA = 'AMARILLA', _('Amarilla')
    ROJA = 'ROJA', _('Roja')


jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='tarjetas')
partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='tarjetas')
tipo = models.CharField(max_length=10, choices=Tipo.choices)
fecha = models.DateTimeField(auto_now_add=True)
multa_pagada = models.BooleanField(default=False)
fecha_pago_multa = models.DateTimeField(blank=True, null=True)

# Campos adicionales
suspension_cumplida = models.BooleanField(default=False)
minuto = models.PositiveSmallIntegerField(blank=True, null=True)
motivo = models.TextField(blank=True, max_length=200)


def __str__(self):
    return f"{self.jugador} - {self.tipo} - {self.partido}"


def save(self, *args, **kwargs):
    super().save(*args, **kwargs)

    # Verificar suspension por tarjeta roja
    if self.tipo == 'ROJA' and not self.jugador.suspendido:
        partidos_suspension = self.jugador.equipo.categoria.partidos_suspension_roja
        self.jugador.suspendido = True
        self.jugador.partidos_suspension_restantes = partidos_suspension
        self.jugador.save()

    # Verificar suspension por acumulación de amarillas
    elif self.tipo == 'AMARILLA':
        self.jugador.verificar_suspension_por_amarillas()


@property
def monto_multa(self):
    """Retorna el monto de la multa según el tipo de tarjeta"""
    if self.tipo == 'AMARILLA':
        return self.jugador.equipo.categoria.multa_amarilla
    return self.jugador.equipo.categoria.multa_roja


class Meta:
    verbose_name = "Tarjeta"
    verbose_name_plural = "Tarjetas"
    ordering = ['-fecha']


class CambioJugador(models.Model):
    """Registro de cambios de jugadores durante partidos"""


partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='cambios')
jugador_sale = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='cambios_sale')
jugador_entra = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='cambios_entra')
minuto = models.PositiveSmallIntegerField()


def clean(self):
    if self.jugador_sale.equipo != self.jugador_entra.equipo:
        raise ValidationError('Los jugadores deben ser del mismo equipo')

    cambios_equipo = CambioJugador.objects.filter(
        partido=self.partido,
        jugador_sale__equipo=self.jugador_sale.equipo
    ).count()

    if cambios_equipo >= 3:
        raise ValidationError('No se pueden hacer más de 3 cambios por equipo')


def __str__(self):
    return f"{self.partido}: {self.jugador_sale} → {self.jugador_entra}"


class Meta:
    verbose_name = "Cambio de Jugador"
    verbose_name_plural = "Cambios de Jugadores"


class EventoPartido(models.Model):
    """Eventos especiales durante partidos"""


class TipoEvento(models.TextChoices):
    SUSPENSION = 'SUSPENSION', _('Suspensión')
    GRESCA = 'GRESCA', _('Gresca')
    INVASION = 'INVASION', _('Invasión de público')
    ABANDONO = 'ABANDONO', _('Abandono de equipo')
    DIFERENCIA_8_GOLES = 'DIFERENCIA_8', _('Diferencia de 8 goles')


partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='eventos')
tipo = models.CharField(max_length=20, choices=TipoEvento.choices)
descripcion = models.TextField()
minuto = models.PositiveSmallIntegerField(blank=True, null=True)
equipo_responsable = models.ForeignKey(Equipo, on_delete=models.CASCADE, blank=True, null=True)


def __str__(self):
    return f"{self.partido} - {self.tipo}"


class Meta:
    verbose_name = "Evento de Partido"
    verbose_name_plural = "Eventos de Partidos"


class EstadisticaEquipo(models.Model):
    """Estadísticas de equipos en el torneo"""


equipo = models.OneToOneField(Equipo, on_delete=models.CASCADE, related_name='estadisticas')
torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='estadisticas')
# Estadísticas de fase de grupos
partidos_jugados = models.PositiveSmallIntegerField(default=0)
partidos_ganados = models.PositiveSmallIntegerField(default=0)
partidos_empatados = models.PositiveSmallIntegerField(default=0)
partidos_perdidos = models.PositiveSmallIntegerField(default=0)
goles_favor = models.PositiveSmallIntegerField(default=0)
goles_contra = models.PositiveSmallIntegerField(default=0)
diferencia_goles = models.IntegerField(default=0)
puntos = models.PositiveSmallIntegerField(default=0)

# Estadísticas adicionales
tarjetas_amarillas = models.PositiveSmallIntegerField(default=0)
tarjetas_rojas = models.PositiveSmallIntegerField(default=0)


def __str__(self):
    return f"{self.equipo.nombre} - {self.torneo.nombre}"


def actualizar_estadisticas(self):
    """Actualiza las estadísticas basándose en los partidos jugados"""
    partidos = Partido.objects.filter(
        Q(equipo_1=self.equipo) | Q(equipo_2=self.equipo),
        torneo=self.torneo,
        jugado=True,
        es_eliminatorio=False
    )

    self.partidos_jugados = partidos.count()
    self.partidos_ganados = 0
    self.partidos_empatados = 0
    self.partidos_perdidos = 0
    self.goles_favor = 0
    self.goles_contra = 0
    self.puntos = 0

    for partido in partidos:
        if partido.equipo_1 == self.equipo:
            self.goles_favor += partido.goles_equipo_1
            self.goles_contra += partido.goles_equipo_2

            if partido.goles_equipo_1 > partido.goles_equipo_2:
                self.partidos_ganados += 1
                self.puntos += 3
            elif partido.goles_equipo_1 == partido.goles_equipo_2:
                self.partidos_empatados += 1
                self.puntos += 1
            else:
                self.partidos_perdidos += 1
        else:
            self.goles_favor += partido.goles_equipo_2
            self.goles_contra += partido.goles_equipo_1

            if partido.goles_equipo_2 > partido.goles_equipo_1:
                self.partidos_ganados += 1
                self.puntos += 3
            elif partido.goles_equipo_2 == partido.goles_equipo_1:
                self.partidos_empatados += 1
                self.puntos += 1
            else:
                self.partidos_perdidos += 1

    self.diferencia_goles = self.goles_favor - self.goles_contra

    # Actualizar tarjetas
    self.tarjetas_amarillas = Tarjeta.objects.filter(
        jugador__equipo=self.equipo,
        partido__torneo=self.torneo,
        tipo='AMARILLA'
    ).count()

    self.tarjetas_rojas = Tarjeta.objects.filter(
        jugador__equipo=self.equipo,
        partido__torneo=self.torneo,
        tipo='ROJA'
    ).count()

    self.save()


class Meta:
    unique_together = ['equipo', 'torneo']
    verbose_name = "Estadística de Equipo"
    verbose_name_plural = "Estadísticas de Equipos"
    ordering = ['-puntos', '-diferencia_goles', '-goles_favor']


class LlaveEliminatoria(models.Model):
    """Llaves de eliminación directa"""


fase = models.ForeignKey(FaseEliminatoria, on_delete=models.CASCADE, related_name='llaves')
numero_llave = models.PositiveSmallIntegerField()
equipo_1 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='llaves_como_equipo_1', blank=True,
                             null=True)
equipo_2 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='llaves_como_equipo_2', blank=True,
                             null=True)
partido = models.OneToOneField(Partido, on_delete=models.CASCADE, related_name='llave', blank=True, null=True)
completada = models.BooleanField(default=False)


def __str__(self):
    return f"{self.fase.nombre} - Llave {self.numero_llave}"


def generar_partido(self):
    """Genera el partido para esta llave"""
    if self.equipo_1 and self.equipo_2 and not self.partido:
        self.partido = Partido.objects.create(
            torneo=self.fase.torneo,
            fase_eliminatoria=self.fase,
            equipo_1=self.equipo_1,
            equipo_2=self.equipo_2,
            es_eliminatorio=True,
            fecha=timezone.now()
        )
        self.save()


@property
def ganador(self):
    """Retorna el ganador de la llave"""
    if self.partido and self.partido.equipo_ganador:
        return self.partido.equipo_ganador
    return None


class Meta:
    unique_together = ['fase', 'numero_llave']
    ordering = ['numero_llave']
    verbose_name = "Llave Eliminatoria"
    verbose_name_plural = "Llaves Eliminatorias"


class MejorPerdedor(models.Model):
    """Tracking de mejores perdedores por grupo"""


torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='mejores_perdedores')
grupo = models.CharField(max_length=1)
equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
puntos = models.PositiveSmallIntegerField()
diferencia_goles = models.IntegerField()
goles_contra = models.PositiveSmallIntegerField()
goles_favor = models.PositiveSmallIntegerField()


class Meta:
    unique_together = ['torneo', 'grupo', 'equipo']
    ordering = ['grupo', '-puntos', '-diferencia_goles', 'goles_contra']
    verbose_name = "Mejor Perdedor"
    verbose_name_plural = "Mejores Perdedores"


class EventoTorneo(models.Model):
    """Eventos importantes del torneo"""


class TipoEvento(models.TextChoices):
    INICIO_INSCRIPCION = 'inicio_inscripcion', _('Inicio de Inscripción')


FIN_INSCRIPCION = 'fin_inscripcion', _('Fin de Inscripción')
INICIO_GRUPOS = 'inicio_grupos', _('Inicio Fase de Grupos')
FIN_GRUPOS = 'fin_grupos', _('Fin Fase de Grupos')
INICIO_ELIMINATORIAS = 'inicio_eliminatorias', _('Inicio Eliminatorias')
FINAL_TORNEO = 'final_torneo', _('Final del Torneo')
CLASIFICACION_EQUIPOS = 'clasificacion', _('Clasificación de Equipos')
EXCLUSION_EQUIPO = 'exclusion', _('Exclusión de Equipo')
torneo = models.ForeignKey(Torneo, on_delete=models.CASCADE, related_name='eventos')
tipo = models.CharField(max_length=30, choices=TipoEvento.choices)
descripcion = models.TextField()
fecha = models.DateTimeField(auto_now_add=True)
equipo_involucrado = models.ForeignKey(Equipo, on_delete=models.CASCADE, blank=True, null=True)
datos_adicionales = models.JSONField(blank=True, null=True)


def __str__(self):
    return f"{self.torneo.nombre} - {self.get_tipo_display()}"


class Meta:
    ordering = ['-fecha']
    verbose_name = "Evento del Torneo"
    verbose_name_plural = "Eventos del Torneo"
