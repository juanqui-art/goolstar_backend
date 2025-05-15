"""
Pruebas para los modelos de competición del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta, date
from api.models.base import Categoria, Torneo
from api.models.participantes import Equipo, Jugador, Arbitro
from api.models.competicion import Jornada, Partido, Gol, Tarjeta, CambioJugador, EventoPartido
from api.utils.date_utils import date_to_datetime  # Importar utilidad para fechas con zona horaria


class JornadaModelTest(TestCase):
    """Pruebas para el modelo Jornada."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.jornada = Jornada.objects.create(
            nombre="Jornada 1",
            numero=1,
            fecha=timezone.now().date()
        )

    def test_jornada_creation(self):
        """Verifica que la jornada se crea correctamente."""
        self.assertEqual(self.jornada.nombre, "Jornada 1")
        self.assertEqual(self.jornada.numero, 1)
        self.assertFalse(self.jornada.activa)

    def test_jornada_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.jornada), "Jornada 1")


class PartidoModelTest(TestCase):
    """Pruebas para el modelo Partido."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            costo_inscripcion=100.00
        )
        
        self.torneo = Torneo.objects.create(
            nombre="Torneo Apertura 2025",
            categoria=self.categoria,
            fecha_inicio=timezone.now().date()
        )
        
        self.equipo1 = Equipo.objects.create(
            nombre="Real Madrid",
            categoria=self.categoria,
            torneo=self.torneo,
            grupo="A"
        )
        
        self.equipo2 = Equipo.objects.create(
            nombre="Barcelona",
            categoria=self.categoria,
            torneo=self.torneo,
            grupo="B"
        )
        
        self.arbitro = Arbitro.objects.create(
            nombres="Roberto",
            apellidos="Martínez"
        )
        
        self.jornada = Jornada.objects.create(
            nombre="Jornada 1",
            numero=1
        )
        
        self.partido = Partido.objects.create(
            torneo=self.torneo,
            jornada=self.jornada,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2,
            arbitro=self.arbitro,
            fecha=timezone.now() + timedelta(days=7),
            cancha="Estadio Principal"
        )

    def test_partido_creation(self):
        """Verifica que el partido se crea correctamente."""
        self.assertEqual(self.partido.torneo, self.torneo)
        self.assertEqual(self.partido.jornada, self.jornada)
        self.assertEqual(self.partido.equipo_1, self.equipo1)
        self.assertEqual(self.partido.equipo_2, self.equipo2)
        self.assertEqual(self.partido.arbitro, self.arbitro)
        self.assertEqual(self.partido.cancha, "Estadio Principal")
        self.assertFalse(self.partido.completado)
        self.assertEqual(self.partido.goles_equipo_1, 0)
        self.assertEqual(self.partido.goles_equipo_2, 0)
        self.assertFalse(self.partido.es_eliminatorio)

    def test_partido_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        # Partido no completado
        self.assertTrue(f"{self.equipo1.nombre} vs {self.equipo2.nombre}" in str(self.partido))
        
        # Partido completado
        self.partido.completado = True
        self.partido.goles_equipo_1 = 2
        self.partido.goles_equipo_2 = 1
        self.partido.save()
        self.assertEqual(str(self.partido), "Real Madrid 2 - 1 Barcelona")

    def test_resultado(self):
        """Verifica que el método resultado funcione correctamente."""
        # Partido no completado
        self.assertEqual(self.partido.resultado, "Pendiente")
        
        # Partido completado
        self.partido.completado = True
        self.partido.goles_equipo_1 = 2
        self.partido.goles_equipo_2 = 1
        self.partido.save()
        self.assertEqual(self.partido.resultado, "2 - 1")
        
        # Partido eliminatorio con penales
        self.partido.es_eliminatorio = True
        self.partido.penales_equipo_1 = 5
        self.partido.penales_equipo_2 = 4
        self.partido.save()
        self.assertEqual(self.partido.resultado, "2 - 1 (Penales: 5 - 4)")

    def test_arbitro_asignado(self):
        """Verifica que el método arbitro_asignado funcione correctamente."""
        self.assertEqual(self.partido.arbitro_asignado, "Roberto Martínez")
        
        # Sin árbitro asignado
        self.partido.arbitro = None
        self.partido.save()
        self.assertEqual(self.partido.arbitro_asignado, "Sin asignar")

    def test_es_fase_grupos(self):
        """Verifica que el método es_fase_grupos funcione correctamente."""
        self.assertTrue(self.partido.es_fase_grupos)
        
        # Partido de fase eliminatoria
        self.partido.jornada = None
        self.partido.fase_eliminatoria = None  # En un caso real, aquí se asignaría una fase eliminatoria
        self.partido.save()
        self.assertFalse(self.partido.es_fase_grupos)

    def test_marcar_inasistencia(self):
        """Verifica que el método marcar_inasistencia funcione correctamente."""
        # Marcar inasistencia del equipo 1
        self.partido.marcar_inasistencia(self.equipo1)
        self.assertTrue(self.partido.inasistencia_equipo_1)
        self.assertFalse(self.partido.inasistencia_equipo_2)
        self.assertEqual(self.partido.goles_equipo_2, 3)  # Victoria por default
        self.assertTrue(self.partido.completado)
        self.assertEqual(self.equipo1.inasistencias, 1)
        
        # Reiniciar para probar con equipo 2
        self.partido.inasistencia_equipo_1 = False
        self.partido.goles_equipo_2 = 0
        self.partido.completado = False
        self.partido.save()
        self.equipo1.inasistencias = 0
        self.equipo1.save()
        
        # Marcar inasistencia del equipo 2
        self.partido.marcar_inasistencia(self.equipo2)
        self.assertFalse(self.partido.inasistencia_equipo_1)
        self.assertTrue(self.partido.inasistencia_equipo_2)
        self.assertEqual(self.partido.goles_equipo_1, 3)  # Victoria por default
        self.assertTrue(self.partido.completado)
        self.assertEqual(self.equipo2.inasistencias, 1)


class GolModelTest(TestCase):
    """Pruebas para el modelo Gol."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES")
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        self.equipo = Equipo.objects.create(nombre="Equipo", categoria=self.categoria, torneo=self.torneo)
        self.jugador = Jugador.objects.create(
            primer_nombre="Carlos", primer_apellido="Gómez", 
            cedula="1234567890", equipo=self.equipo, numero_dorsal=10
        )
        self.partido = Partido.objects.create(
            torneo=self.torneo, equipo_1=self.equipo, 
            equipo_2=Equipo.objects.create(nombre="Rival", categoria=self.categoria, torneo=self.torneo),
            fecha=timezone.now()
        )
        self.gol = Gol.objects.create(
            jugador=self.jugador,
            partido=self.partido,
            minuto=35,
            autogol=False
        )

    def test_gol_creation(self):
        """Verifica que el gol se crea correctamente."""
        self.assertEqual(self.gol.jugador, self.jugador)
        self.assertEqual(self.gol.partido, self.partido)
        self.assertEqual(self.gol.minuto, 35)
        self.assertFalse(self.gol.autogol)

    def test_gol_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.gol), f"Gol de {self.jugador} (35)")
        
        # Gol sin minuto registrado
        self.gol.minuto = None
        self.gol.save()
        self.assertEqual(str(self.gol), f"Gol de {self.jugador} (min ?)")


class TarjetaModelTest(TestCase):
    """Pruebas para el modelo Tarjeta."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES", 
            multa_amarilla=2.00,
            multa_roja=5.00,
            partidos_suspension_roja=2
        )
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        self.equipo = Equipo.objects.create(nombre="Equipo", categoria=self.categoria, torneo=self.torneo)
        self.jugador = Jugador.objects.create(
            primer_nombre="Carlos", primer_apellido="Gómez", 
            cedula="1234567890", equipo=self.equipo, numero_dorsal=10
        )
        self.partido = Partido.objects.create(
            torneo=self.torneo, equipo_1=self.equipo, 
            equipo_2=Equipo.objects.create(nombre="Rival", categoria=self.categoria, torneo=self.torneo),
            fecha=timezone.now()
        )

    def test_tarjeta_amarilla_creation(self):
        """Verifica que la tarjeta amarilla se crea correctamente."""
        tarjeta = Tarjeta.objects.create(
            jugador=self.jugador,
            partido=self.partido,
            tipo=Tarjeta.Tipo.AMARILLA,
            minuto=40,
            motivo="Falta táctica"
        )
        
        self.assertEqual(tarjeta.jugador, self.jugador)
        self.assertEqual(tarjeta.partido, self.partido)
        self.assertEqual(tarjeta.tipo, "AMARILLA")
        self.assertEqual(tarjeta.minuto, 40)
        self.assertEqual(tarjeta.motivo, "Falta táctica")
        self.assertFalse(tarjeta.pagada)
        self.assertFalse(tarjeta.suspension_cumplida)

    def test_tarjeta_roja_creation(self):
        """Verifica que la tarjeta roja se crea correctamente y suspende al jugador."""
        tarjeta = Tarjeta.objects.create(
            jugador=self.jugador,
            partido=self.partido,
            tipo=Tarjeta.Tipo.ROJA,
            minuto=75,
            motivo="Agresión"
        )
        
        # Refrescar el jugador desde la base de datos
        self.jugador.refresh_from_db()
        
        self.assertEqual(tarjeta.tipo, "ROJA")
        self.assertTrue(self.jugador.suspendido)
        self.assertEqual(self.jugador.partidos_suspension_restantes, 2)  # Según la categoría

    def test_monto_multa(self):
        """Verifica que el método monto_multa funcione correctamente."""
        tarjeta_amarilla = Tarjeta.objects.create(
            jugador=self.jugador,
            partido=self.partido,
            tipo=Tarjeta.Tipo.AMARILLA
        )
        
        tarjeta_roja = Tarjeta.objects.create(
            jugador=self.jugador,
            partido=self.partido,
            tipo=Tarjeta.Tipo.ROJA
        )
        
        self.assertEqual(tarjeta_amarilla.monto_multa, 2.00)
        self.assertEqual(tarjeta_roja.monto_multa, 5.00)


class EventoPartidoModelTest(TestCase):
    """Pruebas para el modelo EventoPartido."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="Categoría Test")
        # Añadir fecha_inicio al crear el torneo
        self.torneo = Torneo.objects.create(
            nombre="Torneo Test", 
            categoria=self.categoria,
            fecha_inicio=date(2025, 5, 13)
        )
        
        self.equipo = Equipo.objects.create(nombre="Equipo", categoria=self.categoria, torneo=self.torneo)
        
        # Usar una fecha fija para el test en lugar de timezone.now()
        test_date = date_to_datetime(date(2025, 5, 13))
        self.partido = Partido.objects.create(
            torneo=self.torneo, equipo_1=self.equipo, 
            equipo_2=Equipo.objects.create(nombre="Rival", categoria=self.categoria, torneo=self.torneo),
            fecha=test_date
        )
        
        self.evento = EventoPartido.objects.create(
            partido=self.partido,
            tipo=EventoPartido.TipoEvento.SUSPENSION,
            descripcion="Partido suspendido por lluvia",
            minuto=65,
            equipo_responsable=None
        )

    def test_evento_partido_creation(self):
        """Verifica que el evento de partido se crea correctamente."""
        self.assertEqual(self.evento.partido, self.partido)
        self.assertEqual(self.evento.tipo, "SUSPENSION")
        self.assertEqual(self.evento.descripcion, "Partido suspendido por lluvia")
        self.assertEqual(self.evento.minuto, 65)
        self.assertIsNone(self.evento.equipo_responsable)

    def test_evento_partido_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.evento), "Suspensión - Equipo vs Rival (13/05/2025)")
