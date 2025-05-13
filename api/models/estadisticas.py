"""
Modelos de estadísticas para el sistema GoolStar.
Incluye estadísticas de equipos, llaves eliminatorias y eventos del torneo.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Sum, Count

from .base import Torneo, FaseEliminatoria
from .participantes import Equipo


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
        return f"Estadísticas de {self.equipo.nombre}"

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas basándose en los partidos jugados"""
        from .competicion import Partido, Tarjeta
        
        # Reiniciar estadísticas
        self.partidos_jugados = 0
        self.partidos_ganados = 0
        self.partidos_empatados = 0
        self.partidos_perdidos = 0
        self.goles_favor = 0
        self.goles_contra = 0
        
        # Obtener todos los partidos completados del equipo en este torneo
        partidos_local = Partido.objects.filter(
            equipo_1=self.equipo,
            torneo=self.torneo,
            completado=True
        )
        
        partidos_visitante = Partido.objects.filter(
            equipo_2=self.equipo,
            torneo=self.torneo,
            completado=True
        )
        
        # Procesar partidos como local
        for partido in partidos_local:
            self.partidos_jugados += 1
            self.goles_favor += partido.goles_equipo_1
            self.goles_contra += partido.goles_equipo_2
            
            if partido.goles_equipo_1 > partido.goles_equipo_2:
                self.partidos_ganados += 1
            elif partido.goles_equipo_1 < partido.goles_equipo_2:
                self.partidos_perdidos += 1
            else:
                self.partidos_empatados += 1
        
        # Procesar partidos como visitante
        for partido in partidos_visitante:
            self.partidos_jugados += 1
            self.goles_favor += partido.goles_equipo_2
            self.goles_contra += partido.goles_equipo_1
            
            if partido.goles_equipo_2 > partido.goles_equipo_1:
                self.partidos_ganados += 1
            elif partido.goles_equipo_2 < partido.goles_equipo_1:
                self.partidos_perdidos += 1
            else:
                self.partidos_empatados += 1
        
        # Calcular diferencia de goles y puntos
        self.diferencia_goles = self.goles_favor - self.goles_contra
        self.puntos = (self.partidos_ganados * 3) + self.partidos_empatados
        
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
    partido = models.OneToOneField('api.Partido', on_delete=models.CASCADE, related_name='llave', blank=True, null=True)
    completada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.fase.nombre} - Llave {self.numero_llave}"

    def generar_partido(self):
        """Genera el partido para esta llave"""
        from .competicion import Partido
        
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
        if self.partido and self.partido.completado:
            if self.partido.goles_equipo_1 > self.partido.goles_equipo_2:
                return self.equipo_1
            elif self.partido.goles_equipo_1 < self.partido.goles_equipo_2:
                return self.equipo_2
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
