"""
Modelos base para el sistema GoolStar.
Incluye categorías, niveles y configuración de torneos.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
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
                                         validators=[MinValueValidator(Decimal('0'))])
    premio_segundo = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                         validators=[MinValueValidator(Decimal('0'))])
    premio_tercero = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                         validators=[MinValueValidator(Decimal('0'))])
    premio_cuarto = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                        validators=[MinValueValidator(Decimal('0'))])
    costo_inscripcion = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True,
                                            validators=[MinValueValidator(Decimal('0'))])
    # Campos para configuración del torneo
    costo_arbitraje = models.DecimalField(max_digits=6, decimal_places=2, default=10.00,
                                          validators=[MinValueValidator(Decimal('0'))])
    multa_amarilla = models.DecimalField(max_digits=6, decimal_places=2, default=2.00,
                                         validators=[MinValueValidator(Decimal('0'))])
    multa_roja = models.DecimalField(max_digits=6, decimal_places=2, default=3.00,
                                     validators=[MinValueValidator(Decimal('0'))])
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
        for grupo in ['A', 'B', 'C', 'D'][:self.numero_grupos]:
            equipos_grupo = self.equipos.filter(
                grupo=grupo,
                activo=True
            ).order_by('-estadisticas__puntos', '-estadisticas__diferencia_goles', '-estadisticas__goles_favor')

            clasificados.extend(list(equipos_grupo[:self.equipos_clasifican_por_grupo]))

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
        return f"{self.torneo.nombre} - {self.torneo.categoria.nombre} - {self.nombre}"

    @property
    def partidos_pendientes(self):
        return self.partidos.filter(completado=False).count()

    @property
    def puede_iniciar_siguiente_fase(self):
        return self.completada or self.partidos_pendientes == 0

    class Meta:
        unique_together = ['torneo', 'orden']
        ordering = ['orden']
        verbose_name = "Fase Eliminatoria"
        verbose_name_plural = "Fases Eliminatorias"
