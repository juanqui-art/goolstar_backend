from django.contrib import admin
from .models import Categoria, Equipo, Jugador, Jornada, Partido, Gol, Tarjeta

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'costo_inscripcion')
    search_fields = ('nombre',)

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'pago_completo', 'abono', 'grupo', 'nivel', 'activo')
    list_filter = ('categoria', 'pago_completo', 'activo', 'grupo')
    search_fields = ('nombre',)

@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cedula', 'equipo', 'nivel')
    list_filter = ('equipo__categoria', 'equipo')
    search_fields = ('primer_nombre', 'primer_apellido', 'cedula')

@admin.register(Jornada)
class JornadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero', 'fecha')
    list_filter = ('fecha',)

@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'jornada', 'fecha', 'goles_equipo_1', 'goles_equipo_2', 'jugado')
    list_filter = ('jornada', 'jugado', 'equipo_1__categoria')
    search_fields = ('equipo_1__nombre', 'equipo_2__nombre')
    date_hierarchy = 'fecha'

@admin.register(Gol)
class GolAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'minuto')
    list_filter = ('partido__jornada', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')

@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'tipo', 'multa_pagada')
    list_filter = ('tipo', 'multa_pagada', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')
