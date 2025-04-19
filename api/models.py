from django.db import models
from django.core.validators import MinValueValidator

NIVEL_CHOICES = [
    (1, '1 - Muy bajo'),
    (2, '2 - Bajo'),
    (3, '3 - Medio'),
    (4, '4 - Alto'),
    (5, '5 - Muy alto'),
]


class Categoria(models.Model):
    """Categorías del torneo: VARONES, DAMAS, MÁSTER"""
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True)
    premio_primero = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    premio_segundo = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    premio_tercero = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    premio_cuarto = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    costo_inscripcion = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])

    def __str__(self):
        return self.nombre


class Equipo(models.Model):
    """Equipos participantes en el torneo"""
    nombre = models.CharField(max_length=100)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='equipos')
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)
    pago_completo = models.BooleanField(default=False)
    abono = models.DecimalField(max_digits=6, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    telefono_contacto = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to='logos_equipos/', blank=True, null=True)
    activo = models.BooleanField(default=True)
    GRUPO_CHOICES = [
        ('A', 'Grupo A'),
        ('B', 'Grupo B'),
    ]
    grupo = models.CharField(max_length=1, choices=GRUPO_CHOICES, blank=True, null=True)
    nivel = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES, blank=True, null=True, verbose_name='Nivel')

    def __str__(self):
        return f"{self.nombre} ({self.categoria.nombre})"

    class Meta:
        unique_together = ['nombre', 'categoria']


class Jugador(models.Model):
    """Jugadores registrados en cada equipo"""
    primer_nombre = models.CharField(max_length=100)
    segundo_nombre = models.CharField(max_length=100, blank=True, null=True)
    primer_apellido = models.CharField(max_length=100)
    segundo_apellido = models.CharField(max_length=100, blank=True, null=True)
    cedula = models.CharField(max_length=15)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='jugadores')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    nivel = models.PositiveSmallIntegerField(choices=NIVEL_CHOICES, blank=True, null=True, verbose_name='Nivel')
    cedula_imagen = models.ImageField(upload_to='cedulas_jugadores/', blank=True, null=True, verbose_name='Imagen de la cédula')

    def __str__(self):
        nombres = f"{self.primer_nombre} {self.segundo_nombre or ''}".strip()
        apellidos = f"{self.primer_apellido} {self.segundo_apellido or ''}".strip()
        return f"{nombres} {apellidos}".strip()

    class Meta:
        unique_together = ['cedula', 'equipo']


class Jornada(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    numero = models.PositiveIntegerField()
    fecha = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.nombre

class Partido(models.Model):
    """Partidos del torneo"""
    jornada = models.ForeignKey(Jornada, on_delete=models.CASCADE, related_name='partidos', blank=True, null=True)
    equipo_1 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_equipo_1')
    equipo_2 = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='partidos_como_equipo_2')
    fecha = models.DateTimeField()
    goles_equipo_1 = models.PositiveSmallIntegerField(default=0)
    goles_equipo_2 = models.PositiveSmallIntegerField(default=0)
    jugado = models.BooleanField(default=False)
    fecha_nombre = models.CharField(max_length=50, blank=True, null=True)

    def clean(self):
        super().clean()
        from django.core.exceptions import ValidationError
        if self.equipo_1 == self.equipo_2:
            raise ValidationError('Los equipos no pueden ser iguales en un partido.')

    def __str__(self):
        return f"{self.equipo_1} vs {self.equipo_2}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Gol(models.Model):
    jugador = models.ForeignKey('Jugador', on_delete=models.CASCADE, related_name='goles')
    partido = models.ForeignKey('Partido', on_delete=models.CASCADE, related_name='goles')
    minuto = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='Minuto (opcional)')

    def __str__(self):
        return f"{self.jugador} - {self.partido}"


class Tarjeta(models.Model):
    """Registro de tarjetas amarillas y rojas"""
    TIPO_CHOICES = [
        ('AMARILLA', 'Amarilla'),
        ('ROJA', 'Roja'),
    ]

    jugador = models.ForeignKey(Jugador, on_delete=models.CASCADE, related_name='tarjetas')
    partido = models.ForeignKey(Partido, on_delete=models.CASCADE, related_name='tarjetas')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    multa_pagada = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.jugador} - {self.tipo}"