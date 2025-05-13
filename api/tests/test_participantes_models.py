"""
Pruebas para los modelos de participantes del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from api.models.base import Nivel, Categoria, Torneo
from api.models.participantes import Dirigente, Equipo, Jugador, Arbitro
from api.models.competicion import Tarjeta


class DirigenteModelTest(TestCase):
    """Pruebas para el modelo Dirigente."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.dirigente = Dirigente.objects.create(
            nombre="Juan Pérez",
            telefono="0987654321"
        )

    def test_dirigente_creation(self):
        """Verifica que el dirigente se crea correctamente."""
        self.assertEqual(self.dirigente.nombre, "Juan Pérez")
        self.assertEqual(self.dirigente.telefono, "0987654321")

    def test_dirigente_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.dirigente), "Juan Pérez")


class EquipoModelTest(TestCase):
    """Pruebas para el modelo Equipo."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            costo_inscripcion=Decimal('100.00'),
            multa_amarilla=Decimal('2.00'),
            multa_roja=Decimal('5.00')
        )
        
        self.torneo = Torneo.objects.create(
            nombre="Torneo Apertura 2025",
            categoria=self.categoria,
            fecha_inicio=timezone.now().date()
        )
        
        self.dirigente = Dirigente.objects.create(
            nombre="Juan Pérez",
            telefono="0987654321"
        )
        
        self.equipo = Equipo.objects.create(
            nombre="Real Madrid",
            categoria=self.categoria,
            torneo=self.torneo,
            dirigente=self.dirigente,
            grupo="A",
            nivel=Nivel.ALTO
        )

    def test_equipo_creation(self):
        """Verifica que el equipo se crea correctamente."""
        self.assertEqual(self.equipo.nombre, "Real Madrid")
        self.assertEqual(self.equipo.categoria, self.categoria)
        self.assertEqual(self.equipo.torneo, self.torneo)
        self.assertEqual(self.equipo.dirigente, self.dirigente)
        self.assertEqual(self.equipo.grupo, "A")
        self.assertEqual(self.equipo.nivel, Nivel.ALTO)
        self.assertTrue(self.equipo.activo)
        self.assertEqual(self.equipo.inasistencias, 0)

    def test_equipo_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.equipo), "Real Madrid")

    def test_get_total_inscripcion(self):
        """Verifica que el método get_total_inscripcion funcione correctamente."""
        # Inicialmente, el total de inscripción debe ser igual al costo de inscripción
        self.assertEqual(self.equipo.get_total_inscripcion(), Decimal('100.00'))

    def test_verificar_suspension_por_inasistencias(self):
        """Verifica que el método verificar_suspension_por_inasistencias funcione correctamente."""
        # Inicialmente no debe estar excluido
        self.assertFalse(self.equipo.excluido_por_inasistencias)
        
        # Aumentar inasistencias por debajo del límite
        self.equipo.inasistencias = 2
        self.equipo.save()
        self.equipo.verificar_suspension_por_inasistencias()
        self.assertFalse(self.equipo.excluido_por_inasistencias)
        self.assertTrue(self.equipo.activo)
        
        # Aumentar inasistencias al límite
        self.equipo.inasistencias = 3
        self.equipo.save()
        self.equipo.verificar_suspension_por_inasistencias()
        self.assertTrue(self.equipo.excluido_por_inasistencias)
        self.assertFalse(self.equipo.activo)


class JugadorModelTest(TestCase):
    """Pruebas para el modelo Jugador."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            limite_amarillas_suspension=3
        )
        
        self.torneo = Torneo.objects.create(
            nombre="Torneo Apertura 2025",
            categoria=self.categoria,
            fecha_inicio=timezone.now().date()
        )
        
        self.equipo = Equipo.objects.create(
            nombre="Real Madrid",
            categoria=self.categoria,
            torneo=self.torneo,
            grupo="A"
        )
        
        self.jugador = Jugador.objects.create(
            primer_nombre="Carlos",
            segundo_nombre="Alberto",
            primer_apellido="Gómez",
            segundo_apellido="Pérez",
            cedula="1234567890",
            equipo=self.equipo,
            numero_dorsal=10,
            posicion="Delantero",
            nivel=Nivel.ALTO
        )

    def test_jugador_creation(self):
        """Verifica que el jugador se crea correctamente."""
        self.assertEqual(self.jugador.primer_nombre, "Carlos")
        self.assertEqual(self.jugador.segundo_nombre, "Alberto")
        self.assertEqual(self.jugador.primer_apellido, "Gómez")
        self.assertEqual(self.jugador.segundo_apellido, "Pérez")
        self.assertEqual(self.jugador.cedula, "1234567890")
        self.assertEqual(self.jugador.equipo, self.equipo)
        self.assertEqual(self.jugador.numero_dorsal, 10)
        self.assertEqual(self.jugador.posicion, "Delantero")
        self.assertEqual(self.jugador.nivel, Nivel.ALTO)
        self.assertFalse(self.jugador.suspendido)

    def test_jugador_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.jugador), "Gómez Pérez Carlos")

    def test_nombre_completo(self):
        """Verifica que el método nombre_completo funcione correctamente."""
        self.assertEqual(self.jugador.nombre_completo, "Carlos Alberto Gómez Pérez")
        
        # Probar sin segundo nombre
        self.jugador.segundo_nombre = None
        self.assertEqual(self.jugador.nombre_completo, "Carlos Gómez Pérez")
        
        # Probar sin segundo apellido
        self.jugador.segundo_nombre = "Alberto"
        self.jugador.segundo_apellido = None
        self.assertEqual(self.jugador.nombre_completo, "Carlos Alberto Gómez")

    def test_puede_jugar(self):
        """Verifica que el método puede_jugar funcione correctamente."""
        # Inicialmente puede jugar
        self.assertTrue(self.jugador.puede_jugar)
        
        # Suspender al jugador
        self.jugador.suspendido = True
        self.jugador.save()
        self.assertFalse(self.jugador.puede_jugar)


class ArbitroModelTest(TestCase):
    """Pruebas para el modelo Arbitro."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.arbitro = Arbitro.objects.create(
            nombres="Roberto",
            apellidos="Martínez",
            telefono="0987654321",
            email="roberto@example.com",
            experiencia_anos=5,
            categoria_maxima="Primera División"
        )

    def test_arbitro_creation(self):
        """Verifica que el árbitro se crea correctamente."""
        self.assertEqual(self.arbitro.nombres, "Roberto")
        self.assertEqual(self.arbitro.apellidos, "Martínez")
        self.assertEqual(self.arbitro.telefono, "0987654321")
        self.assertEqual(self.arbitro.email, "roberto@example.com")
        self.assertEqual(self.arbitro.experiencia_anos, 5)
        self.assertEqual(self.arbitro.categoria_maxima, "Primera División")
        self.assertTrue(self.arbitro.activo)

    def test_arbitro_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.arbitro), "Martínez, Roberto")

    def test_nombre_completo(self):
        """Verifica que el método nombre_completo funcione correctamente."""
        self.assertEqual(self.arbitro.nombre_completo, "Roberto Martínez")
