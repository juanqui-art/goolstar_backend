from django.contrib import admin

# Importaciones de modelos base
from .models.base import Categoria, Torneo, FaseEliminatoria

# Importaciones de modelos de participantes
from .models.participantes import Equipo, Jugador, Dirigente, Arbitro

# Importaciones de modelos de competición
from .models.competicion import Jornada, Partido, Gol, Tarjeta, CambioJugador, EventoPartido

# Importaciones de modelos de estadísticas
from .models.estadisticas import EstadisticaEquipo, LlaveEliminatoria, MejorPerdedor, EventoTorneo

# Importaciones de modelos financieros
from .models.financiero import TransaccionPago, PagoArbitro

# Importaciones de modelos de participación
from .models.participacion import ParticipacionJugador

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'costo_inscripcion')
    search_fields = ('nombre',)

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'grupo', 'nivel', 'activo')
    list_filter = ('categoria', 'activo', 'grupo')
    search_fields = ('nombre',)

@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'cedula', 'equipo', 'nivel')
    list_filter = ('equipo__categoria', 'equipo')
    search_fields = ('primer_nombre', 'primer_apellido', 'cedula')
    ordering = ('primer_apellido',)
    list_per_page = 25

@admin.register(Jornada)
class JornadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero', 'fecha')
    list_filter = ('fecha',)

class GolInline(admin.TabularInline):
    model = Gol
    extra = 1

@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'jornada', 'fecha', 'goles_equipo_1', 'goles_equipo_2', 'completado')
    list_filter = ('jornada', 'completado', 'equipo_1__categoria')
    search_fields = ('equipo_1__nombre', 'equipo_2__nombre')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_per_page = 25
    inlines = [GolInline]

@admin.register(Gol)
class GolAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'minuto')
    list_filter = ('partido__jornada', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')

@admin.register(Tarjeta)
class TarjetaAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'tipo', 'pagada')
    list_filter = ('tipo', 'pagada', 'jugador__equipo')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'fecha_inicio', 'fase_actual', 'activo', 'finalizado')
    list_filter = ('categoria', 'activo', 'finalizado')
    search_fields = ('nombre',)


@admin.register(FaseEliminatoria)
class FaseEliminatoriaAdmin(admin.ModelAdmin):
    list_display = ('torneo', 'nombre', 'orden', 'fecha_inicio', 'fecha_fin', 'completada')
    list_filter = ('torneo', 'completada')
    search_fields = ('nombre',)


@admin.register(Dirigente)
class DirigenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono')
    search_fields = ('nombre', 'telefono')


@admin.register(Arbitro)
class ArbitroAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'telefono', 'email', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombres', 'apellidos', 'telefono')


@admin.register(CambioJugador)
class CambioJugadorAdmin(admin.ModelAdmin):
    list_display = ('partido', 'jugador_sale', 'jugador_entra', 'minuto')
    list_filter = ('partido__jornada',)
    search_fields = ('jugador_sale__primer_apellido', 'jugador_entra__primer_apellido')


@admin.register(EventoPartido)
class EventoPartidoAdmin(admin.ModelAdmin):
    list_display = ('partido', 'tipo', 'minuto', 'equipo_responsable')
    list_filter = ('tipo',)
    search_fields = ('descripcion',)


@admin.register(EstadisticaEquipo)
class EstadisticaEquipoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'torneo', 'partidos_jugados', 'partidos_ganados', 'puntos', 'goles_favor', 'goles_contra')
    list_filter = ('torneo',)
    search_fields = ('equipo__nombre',)


@admin.register(LlaveEliminatoria)
class LlaveEliminatoriaAdmin(admin.ModelAdmin):
    list_display = ('fase', 'numero_llave', 'equipo_1', 'equipo_2', 'completada')
    list_filter = ('fase', 'completada')


@admin.register(EventoTorneo)
class EventoTorneoAdmin(admin.ModelAdmin):
    list_display = ('torneo', 'tipo', 'fecha', 'equipo_involucrado')
    list_filter = ('tipo', 'torneo')
    search_fields = ('descripcion',)


@admin.register(TransaccionPago)
class TransaccionPagoAdmin(admin.ModelAdmin):
    list_display = ('equipo', 'tipo', 'fecha', 'monto', 'es_ingreso', 'concepto')
    list_filter = ('tipo',)
    search_fields = ('equipo__nombre', 'concepto')
    date_hierarchy = 'fecha'


@admin.register(PagoArbitro)
class PagoArbitroAdmin(admin.ModelAdmin):
    list_display = ('arbitro', 'partido', 'equipo', 'monto', 'pagado')
    list_filter = ('pagado',)
    search_fields = ('arbitro__nombres', 'arbitro__apellidos')


@admin.register(ParticipacionJugador)
class ParticipacionJugadorAdmin(admin.ModelAdmin):
    list_display = ('jugador', 'partido', 'es_titular', 'numero_dorsal', 'minuto_entra', 'minuto_sale')
    list_filter = ('es_titular', 'partido__jornada')
    search_fields = ('jugador__primer_nombre', 'jugador__primer_apellido')
