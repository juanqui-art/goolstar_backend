"""
Pruebas para los modelos de participación del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from api.models.base import Categoria, Torneo
from api.models.participantes import Equipo, Jugador
from api.models.competicion import Partido
from api.models.participacion import ParticipacionJugador


class ParticipacionJugadorModelTest(TestCase):
    """Pruebas para el modelo ParticipacionJugador."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES")
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        
        self.equipo1 = Equipo.objects.create(nombre="Equipo 1", categoria=self.categoria, torneo=self.torneo)
        self.equipo2 = Equipo.objects.create(nombre="Equipo 2", categoria=self.categoria, torneo=self.torneo)
        
        self.jugador1 = Jugador.objects.create(
            primer_nombre="Carlos", primer_apellido="Gómez", 
            cedula="1234567890", equipo=self.equipo1, numero_dorsal=10
        )
        
        self.jugador2 = Jugador.objects.create(
            primer_nombre="Juan", primer_apellido="Pérez", 
            cedula="0987654321", equipo=self.equipo1, numero_dorsal=7
        )
        
        self.jugador_rival = Jugador.objects.create(
            primer_nombre="Pedro", primer_apellido="López", 
            cedula="5678901234", equipo=self.equipo2, numero_dorsal=9
        )
        
        self.partido = Partido.objects.create(
            torneo=self.torneo, 
            equipo_1=self.equipo1, 
            equipo_2=self.equipo2, 
            fecha=timezone.now()
        )
        
        # Crear participación de jugador titular
        self.participacion_titular = ParticipacionJugador.objects.create(
            partido=self.partido,
            jugador=self.jugador1,
            es_titular=True,
            numero_dorsal=10
        )
        
        # Crear participación de jugador suplente
        self.participacion_suplente = ParticipacionJugador.objects.create(
            partido=self.partido,
            jugador=self.jugador2,
            es_titular=False,
            numero_dorsal=7,
            minuto_entra=60
        )

    def test_participacion_titular_creation(self):
        """Verifica que la participación de jugador titular se crea correctamente."""
        self.assertEqual(self.participacion_titular.partido, self.partido)
        self.assertEqual(self.participacion_titular.jugador, self.jugador1)
        self.assertTrue(self.participacion_titular.es_titular)
        self.assertEqual(self.participacion_titular.numero_dorsal, 10)
        self.assertIsNone(self.participacion_titular.minuto_entra)
        self.assertIsNone(self.participacion_titular.minuto_sale)
        self.assertEqual(self.participacion_titular.motivo_salida, "")

    def test_participacion_suplente_creation(self):
        """Verifica que la participación de jugador suplente se crea correctamente."""
        self.assertEqual(self.participacion_suplente.partido, self.partido)
        self.assertEqual(self.participacion_suplente.jugador, self.jugador2)
        self.assertFalse(self.participacion_suplente.es_titular)
        self.assertEqual(self.participacion_suplente.numero_dorsal, 7)
        self.assertEqual(self.participacion_suplente.minuto_entra, 60)
        self.assertIsNone(self.participacion_suplente.minuto_sale)
        self.assertEqual(self.participacion_suplente.motivo_salida, "")

    def test_participacion_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.participacion_titular), f"{self.jugador1} - {self.partido}")

    def test_minutos_jugados_titular(self):
        """Verifica que el método minutos_jugados funcione correctamente para titulares."""
        # Titular que juega todo el partido
        self.assertEqual(self.participacion_titular.minutos_jugados, 90)
        
        # Titular que sale durante el partido
        self.participacion_titular.minuto_sale = 70
        self.participacion_titular.save()
        self.assertEqual(self.participacion_titular.minutos_jugados, 70)

    def test_minutos_jugados_suplente(self):
        """Verifica que el método minutos_jugados funcione correctamente para suplentes."""
        # Suplente que entra y no sale
        self.assertEqual(self.participacion_suplente.minutos_jugados, 30)  # 90 - 60
        
        # Suplente que entra y sale
        self.participacion_suplente.minuto_sale = 80
        self.participacion_suplente.save()
        self.assertEqual(self.participacion_suplente.minutos_jugados, 20)  # 80 - 60

    def test_salio_durante_partido(self):
        """Verifica que el método salio_durante_partido funcione correctamente."""
        # Inicialmente no salió
        self.assertFalse(self.participacion_titular.salio_durante_partido)
        
        # Marcar salida
        self.participacion_titular.minuto_sale = 70
        self.participacion_titular.save()
        self.assertTrue(self.participacion_titular.salio_durante_partido)

    def test_validacion_jugador_equipo(self):
        """Verifica que se valide que el jugador pertenezca a uno de los equipos del partido."""
        # Crear un jugador de otro equipo que no participa en el partido
        equipo3 = Equipo.objects.create(nombre="Equipo 3", categoria=self.categoria, torneo=self.torneo)
        jugador3 = Jugador.objects.create(
            primer_nombre="Luis", primer_apellido="Rodríguez", 
            cedula="1357924680", equipo=equipo3, numero_dorsal=11
        )
        
        # Intentar crear participación con jugador de equipo que no participa
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=jugador3,
                es_titular=True,
                numero_dorsal=11
            )

    def test_validacion_jugador_suspendido(self):
        """Verifica que se valide que el jugador no esté suspendido."""
        # Suspender al jugador
        self.jugador1.suspendido = True
        self.jugador1.save()
        
        # Intentar crear participación con jugador suspendido
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=self.jugador1,
                es_titular=True,
                numero_dorsal=10
            )

    def test_validacion_dorsal(self):
        """Verifica que se valide que el número de dorsal coincida con el registrado."""
        # Intentar crear participación con dorsal incorrecto
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=self.jugador1,
                es_titular=True,
                numero_dorsal=99  # Dorsal incorrecto
            )

    def test_validacion_minutos(self):
        """Verifica que se valide que los minutos de entrada/salida sean correctos."""
        # Intentar crear participación con minuto de entrada mayor que salida
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=self.jugador_rival,
                es_titular=False,
                numero_dorsal=9,
                minuto_entra=70,
                minuto_sale=60
            )

    def test_validacion_titular_sin_minuto_entrada(self):
        """Verifica que se valide que un titular no tenga minuto de entrada."""
        # Intentar crear participación de titular con minuto de entrada
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=self.jugador_rival,
                es_titular=True,
                numero_dorsal=9,
                minuto_entra=0  # No debería tener minuto de entrada
            )

    def test_validacion_suplente_con_minuto_entrada(self):
        """Verifica que se valide que un suplente tenga minuto de entrada."""
        # Intentar crear participación de suplente sin minuto de entrada
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=self.jugador_rival,
                es_titular=False,
                numero_dorsal=9,
                minuto_entra=None  # Debería tener minuto de entrada
            )

    def test_validacion_motivo_salida(self):
        """Verifica que se valide que si hay motivo de salida, haya minuto de salida."""
        # Intentar crear participación con motivo de salida pero sin minuto
        with self.assertRaises(ValidationError):
            ParticipacionJugador.objects.create(
                partido=self.partido,
                jugador=self.jugador_rival,
                es_titular=True,
                numero_dorsal=9,
                motivo_salida="lesion"  # Tiene motivo pero no minuto de salida
            )
