"""
Modelos de participación para el sistema GoolStar.
Incluye registros de participación de jugadores en partidos.
"""

from django.core.exceptions import ValidationError
from django.db import models

from .participantes import Jugador


class ParticipacionJugador(models.Model):
    """Registro detallado de participación de jugadores en cada partido"""
    # Usamos el string del modelo para evitar dependencias circulares
    # Alternativa: mover este modelo al archivo competicion.py
    partido = models.ForeignKey('api.Partido', on_delete=models.CASCADE, related_name='participaciones')
    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='participaciones')
    es_titular = models.BooleanField(default=True)
    numero_dorsal = models.PositiveSmallIntegerField()

    # Campos para control de entrada/salida
    minuto_entra = models.PositiveSmallIntegerField(blank=True, null=True)
    minuto_sale = models.PositiveSmallIntegerField(blank=True, null=True)
    motivo_salida = models.CharField(max_length=20, blank=True, choices=[
        ('cambio', 'Cambio técnico'),
        ('lesion', 'Lesión'),
        ('tarjeta_roja', 'Tarjeta roja'),
        ('suspension', 'Suspensión'),
    ])

    def clean(self):
        # Validar que el jugador pertenezca a uno de los equipos del partido
        if self.jugador.equipo != self.partido.equipo_1 and self.jugador.equipo != self.partido.equipo_2:
            raise ValidationError("El jugador debe pertenecer a uno de los equipos del partido")

        # Validar que el jugador no esté suspendido
        if self.jugador.suspendido:
            raise ValidationError("El jugador está suspendido y no puede participar")

        # Validar que el número de dorsal coincida con el registrado para el jugador
        if self.numero_dorsal != self.jugador.numero_dorsal:
            raise ValidationError("El número de dorsal debe coincidir con el registrado para el jugador")

        # Validar minutos de entrada/salida
        if self.minuto_entra is not None and self.minuto_sale is not None:
            if self.minuto_entra >= self.minuto_sale:
                raise ValidationError("El minuto de entrada debe ser menor al minuto de salida")

        # Validar que si es titular, no tenga minuto de entrada
        if self.es_titular and self.minuto_entra is not None:
            raise ValidationError("Un jugador titular no debe tener minuto de entrada")

        # Validar que si no es titular, tenga minuto de entrada
        if not self.es_titular and self.minuto_entra is None:
            raise ValidationError("Un jugador suplente debe tener minuto de entrada")

        # Validar que si tiene motivo de salida, tenga minuto de salida
        if self.motivo_salida and self.minuto_sale is None:
            raise ValidationError("Si se especifica motivo de salida, debe indicarse el minuto de salida")

    def save(self, *args, **kwargs):
        # Validar límite de cambios si es un nuevo registro
        if not self.pk and not self.es_titular:
            self.validar_limite_cambios()

        # Guardar el registro
        super().save(*args, **kwargs)

    def validar_limite_cambios(self):
        """Valida que no se excedan los 3 cambios permitidos por equipo"""
        # Contar cambios ya realizados por el equipo
        equipo = self.jugador.equipo
        cambios_realizados = self.partido.get_cambios_realizados(equipo)

        # Verificar si se excede el límite
        if cambios_realizados >= 3:
            raise ValidationError(f"El equipo {equipo.nombre} ya ha realizado el máximo de 3 cambios permitidos")

    @property
    def minutos_jugados(self):
        """Calcula los minutos jugados por el jugador"""
        if self.es_titular:
            if self.minuto_sale:
                return self.minuto_sale
            return 90  # Duración estándar de un partido
        elif self.minuto_entra:
            if self.minuto_sale:
                return self.minuto_sale - self.minuto_entra
            return 90 - self.minuto_entra
        return 0

    @property
    def salio_durante_partido(self):
        """Indica si el jugador salió antes del final del partido"""
        return self.minuto_sale is not None

    def __str__(self):
        return f"{self.jugador} - {self.partido}"

    class Meta:
        unique_together = [
            ['partido', 'jugador']
        ]
        # No podemos usar jugador__equipo en unique_together, necesitamos un índice personalizado
        verbose_name = "Participación de Jugador"
        verbose_name_plural = "Participaciones de Jugadores"
        ordering = ['jugador__equipo', 'numero_dorsal']
