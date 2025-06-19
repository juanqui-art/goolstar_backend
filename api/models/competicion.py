"""
Modelos de competición para el sistema GoolStar.
Incluye jornadas, partidos, goles, tarjetas y eventos de partido.
"""

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .base import Torneo, FaseEliminatoria
from .participantes import Equipo, Jugador, Arbitro


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
    fase_eliminatoria = models.ForeignKey(FaseEliminatoria, on_delete=models.CASCADE, related_name='partidos',
                                          blank=True, null=True)
    equipo_1 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_local')
    equipo_2 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_visitante')
    arbitro = models.ForeignKey(Arbitro, on_delete=models.SET_NULL, related_name='partidos', blank=True, null=True)

    # Información del partido
    fecha = models.DateTimeField()
    cancha = models.CharField(max_length=100, blank=True)
    completado = models.BooleanField(default=False)

    # Resultados
    goles_equipo_1 = models.PositiveSmallIntegerField(default=0)
    goles_equipo_2 = models.PositiveSmallIntegerField(default=0)

    # Campos para victoria por default
    MOTIVO_VICTORIA_CHOICES = [
        ('', 'Normal'),
        ('retiro', 'Retiro de equipo'),
        ('inasistencia', 'Inasistencia'),
        ('sancion', 'Sanción administrativa')
    ]
    victoria_por_default = models.CharField(max_length=20, choices=MOTIVO_VICTORIA_CHOICES, blank=True)
    equipo_ganador_default = models.ForeignKey(Equipo, on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name='victorias_por_default')

    # Campos para partidos de eliminación directa
    es_eliminatorio = models.BooleanField(default=False)
    penales_equipo_1 = models.PositiveSmallIntegerField(blank=True, null=True)
    penales_equipo_2 = models.PositiveSmallIntegerField(blank=True, null=True)

    # Campos para control de asistencia
    inasistencia_equipo_1 = models.BooleanField(default=False)
    inasistencia_equipo_2 = models.BooleanField(default=False)

    # Campos para control de pagos
    equipo_1_pago_arbitro = models.BooleanField(default=False)
    equipo_2_pago_arbitro = models.BooleanField(default=False)

    # Campos para acta del partido
    observaciones = models.TextField(blank=True)
    acta_firmada = models.BooleanField(default=False)
    acta_firmada_equipo_1 = models.BooleanField(default=False)
    acta_firmada_equipo_2 = models.BooleanField(default=False)

    # Campos para control de balón
    equipo_pone_balon = models.ForeignKey(Equipo, on_delete=models.SET_NULL, related_name='partidos_con_balon',
                                          blank=True, null=True)

    def clean(self):
        # Validar que no se asigne jornada y fase eliminatoria al mismo tiempo
        if self.jornada and self.fase_eliminatoria:
            raise ValidationError(
                "Un partido no puede pertenecer a una jornada y a una fase eliminatoria simultáneamente")

        # Validar que los equipos sean diferentes, solo si ambos están establecidos
        if hasattr(self, 'equipo_1') and hasattr(self,
                                                 'equipo_2') and self.equipo_1 is not None and self.equipo_2 is not None:
            if self.equipo_1 == self.equipo_2:
                raise ValidationError("Los equipos deben ser diferentes")

    def __str__(self):
        if self.completado:
            return f"{self.equipo_1.nombre} {self.goles_equipo_1} - {self.goles_equipo_2} {self.equipo_2.nombre}"
        return f"{self.equipo_1.nombre} vs {self.equipo_2.nombre} ({self.fecha.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        # Verificar si el partido acaba de ser marcado como completado
        is_newly_completed = False
        if self.pk:
            old_instance = Partido.objects.get(pk=self.pk)
            is_newly_completed = not old_instance.completado and self.completado
        else:
            is_newly_completed = self.completado

        # Guardar el partido
        super().save(*args, **kwargs)

        # Marcamos si el partido fue completado para que lo procese la señal post_save
        if is_newly_completed:
            self._actualizar_estadisticas = True

    def actualizar_estadisticas_post_save(self):
        """Método para actualizar estadísticas después de guardar, 
        diseñado para ser llamado desde una señal post_save"""
        from .estadisticas import EstadisticaEquipo
        from django.db import transaction

        # Usar transacción atómica para la actualización completa
        with transaction.atomic():
            # Asegurar que existen las estadísticas para ambos equipos
            for equipo in [self.equipo_1, self.equipo_2]:
                estadistica, created = EstadisticaEquipo.objects.get_or_create(
                    equipo=equipo,
                    torneo=self.torneo
                )
                estadistica.actualizar_estadisticas()

            # Verificar inasistencias
            if self.inasistencia_equipo_1:
                self.equipo_1.verificar_suspension_por_inasistencias()
            if self.inasistencia_equipo_2:
                self.equipo_2.verificar_suspension_por_inasistencias()

    # Métodos para trabajar con participaciones
    def get_participaciones_equipo(self, equipo):
        """Obtiene todas las participaciones de un equipo en este partido"""
        # Importación local para evitar dependencias circulares
        from .participacion import ParticipacionJugador
        return ParticipacionJugador.objects.filter(partido=self, jugador__equipo=equipo)

    def get_jugadores_titulares(self, equipo):
        """Obtiene jugadores titulares de un equipo"""
        # Importación local para evitar dependencias circulares
        from .participacion import ParticipacionJugador
        return ParticipacionJugador.objects.filter(
            partido=self,
            jugador__equipo=equipo,
            es_titular=True
        ).select_related('jugador')

    def get_jugadores_salen(self, equipo):
        """Obtiene jugadores que salen durante el partido"""
        # Importación local para evitar dependencias circulares
        from .participacion import ParticipacionJugador
        return ParticipacionJugador.objects.filter(
            partido=self,
            jugador__equipo=equipo,
            minuto_sale__isnull=False
        ).select_related('jugador')

    def get_cambios_realizados(self, equipo):
        """Cuenta los cambios realizados por un equipo"""
        # Importación local para evitar dependencias circulares
        from .participacion import ParticipacionJugador
        # Contar jugadores que entraron como cambio
        return ParticipacionJugador.objects.filter(
            partido=self,
            jugador__equipo=equipo,
            es_titular=False,
            minuto_entra__isnull=False
        ).count()

    def validar_minimo_jugadores(self):
        """Valida que cada equipo tenga al menos 4 jugadores"""
        from .participacion import ParticipacionJugador

        for equipo in [self.equipo_1, self.equipo_2]:
            jugadores = ParticipacionJugador.objects.filter(
                partido=self,
                jugador__equipo=equipo
            ).count()

            if jugadores < 4:
                raise ValidationError(f"El equipo {equipo.nombre} debe tener al menos 4 jugadores")

    @property
    def resultado(self):
        """Retorna el resultado del partido incluyendo penales si aplica"""
        if not self.completado:
            return "Pendiente"

        resultado = f"{self.goles_equipo_1} - {self.goles_equipo_2}"

        if self.es_eliminatorio and self.penales_equipo_1 is not None and self.penales_equipo_2 is not None:
            resultado += f" (Penales: {self.penales_equipo_1} - {self.penales_equipo_2})"

        return resultado

    @property
    def arbitro_completamente_pagado(self):
        """Verifica si ambos equipos han pagado al árbitro"""
        return self.equipo_1_pago_arbitro and self.equipo_2_pago_arbitro

    @property
    def arbitro_asignado(self):
        """Retorna el nombre del árbitro o 'Sin asignar'"""
        if self.arbitro:
            return self.arbitro.nombre_completo
        return "Sin asignar"

    @property
    def es_fase_grupos(self):
        """Determina si es partido de fase de grupos"""
        return self.jornada is not None and self.fase_eliminatoria is None

    def marcar_inasistencia(self, equipo):
        """Marca inasistencia de un equipo y actualiza contador"""
        if equipo == self.equipo_1:
            self.inasistencia_equipo_1 = True
            self.goles_equipo_2 = 3  # Victoria por default
            equipo.inasistencias += 1
            equipo.save()
        elif equipo == self.equipo_2:
            self.inasistencia_equipo_2 = True
            self.goles_equipo_1 = 3  # Victoria por default
            equipo.inasistencias += 1
            equipo.save()
        else:
            raise ValueError("El equipo no participa en este partido")

        self.completado = True
        self.save()

        # Verificar si el equipo debe ser excluido
        equipo.verificar_suspension_por_inasistencias()

    class Meta:
        verbose_name = "Partido"
        verbose_name_plural = "Partidos"


class Gol(models.Model):
    """Goles anotados en partidos"""
    jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE, related_name='goles')
    partido = models.ForeignKey('Partido', on_delete=models.CASCADE, related_name='goles')
    minuto = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Minuto (opcional)')
    autogol = models.BooleanField(default=False)

    def __str__(self):
        return f"Gol de {self.jugador} ({self.minuto or 'min ?'})"

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

    # Campos para control de pagos
    pagada = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(blank=True, null=True)

    # Campos adicionales
    suspension_cumplida = models.BooleanField(default=False)
    minuto = models.PositiveSmallIntegerField(blank=True, null=True)
    motivo = models.TextField(blank=True, max_length=200)

    def __str__(self):
        return f"Tarjeta {self.tipo} - {self.jugador}"

    def save(self, *args, **kwargs):
        is_new = not self.pk
        super().save(*args, **kwargs)

        # Si es una tarjeta nueva
        if is_new:
            # Si es roja, suspender al jugador
            if self.tipo == 'ROJA':
                self.jugador.suspendido = True
                self.jugador.partidos_suspension_restantes = self.jugador.equipo.categoria.partidos_suspension_roja
                self.jugador.save()
            # Si es amarilla, verificar acumulación
            elif self.tipo == 'AMARILLA':
                self.jugador.verificar_suspension_por_amarillas()

    @property
    def monto_multa(self):
        """Retorna el monto de la multa según el tipo de tarjeta"""
        if self.tipo == 'AMARILLA':
            return self.jugador.equipo.categoria.multa_amarilla
        elif self.tipo == 'ROJA':
            return self.jugador.equipo.categoria.multa_roja
        return 0

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
        # Validar que ambos jugadores pertenezcan al mismo equipo
        if self.jugador_sale.equipo != self.jugador_entra.equipo:
            raise ValidationError("Los jugadores deben pertenecer al mismo equipo")

        # Validar que el equipo no haya realizado más de 3 cambios
        equipo = self.jugador_sale.equipo
        cambios_realizados = self.partido.get_cambios_realizados(equipo)

        if cambios_realizados >= 3 and not self.pk:  # Si es un nuevo cambio
            raise ValidationError("El equipo ya ha realizado el máximo de 3 cambios permitidos")

    def __str__(self):
        return f"{self.jugador_sale} ↔ {self.jugador_entra} (min {self.minuto})"

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
        return f"{self.get_tipo_display()} - {self.partido}"

    class Meta:
        verbose_name = "Evento de Partido"
        verbose_name_plural = "Eventos de Partidos"
