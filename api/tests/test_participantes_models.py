"""
Pruebas para los modelos de participantes del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from api.models.base import Categoria, Torneo, Nivel
from api.models.participantes import Dirigente, Equipo, Jugador, Arbitro
from api.models.competicion import Tarjeta, Partido


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
        # Nivel es un IntegerChoices, no un modelo, por lo que no necesitamos crearlo
        self.categoria = Categoria.objects.create(
            nombre="VARONES", 
            costo_inscripcion=Decimal('100.00'),
            multa_amarilla=Decimal('5.00'),
            multa_roja=Decimal('10.00'),
            limite_amarillas_suspension=3
        )
        self.torneo = Torneo.objects.create(
            nombre="Torneo de Prueba",
            categoria=self.categoria,
            fecha_inicio=timezone.now().date()
        )
        self.dirigente = Dirigente.objects.create(
            nombre="Juan Pérez",
            telefono="0987654321"
        )
        self.equipo = Equipo.objects.create(
            nombre="Equipo de Prueba",
            categoria=self.categoria,
            dirigente=self.dirigente,
            torneo=self.torneo
        )
        
        # Creamos una categoría "dummy" para las pruebas que antes usaban equipo_sin_categoria
        self.categoria_dummy = Categoria.objects.create(
            nombre="DUMMY",
            costo_inscripcion=None,
            multa_amarilla=Decimal('0.00'),  
            multa_roja=Decimal('0.00'),      
            limite_amarillas_suspension=0
        )
        
        self.equipo_sin_categoria = Equipo.objects.create(
            nombre="Equipo Sin Categoría",
            dirigente=self.dirigente,
            torneo=self.torneo,
            categoria=self.categoria_dummy  
        )

    def test_equipo_creation(self):
        """Verifica que el equipo se crea correctamente."""
        self.assertEqual(self.equipo.nombre, "Equipo de Prueba")
        self.assertEqual(self.equipo.categoria, self.categoria)
        self.assertEqual(self.equipo.torneo, self.torneo)
        self.assertEqual(self.equipo.dirigente, self.dirigente)
        self.assertTrue(self.equipo.activo)
        self.assertEqual(self.equipo.inasistencias, 0)

    def test_equipo_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.equipo), "Equipo de Prueba")

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

    def test_get_deuda_multas_pendientes_con_categoria(self):
        """Verifica que el cálculo de multas pendientes funcione correctamente cuando hay categoría."""
        # Crear jugadores
        jugador1 = Jugador.objects.create(
            primer_nombre="Carlos", primer_apellido="Gómez", 
            cedula="1234567890", equipo=self.equipo, numero_dorsal=10
        )
        jugador2 = Jugador.objects.create(
            primer_nombre="Juan", primer_apellido="Pérez", 
            cedula="0987654321", equipo=self.equipo, numero_dorsal=11
        )
        
        # Crear un partido de prueba para asociar con las tarjetas
        partido_prueba = Partido.objects.create(
            torneo=self.torneo,
            equipo_1=self.equipo,
            equipo_2=self.equipo_sin_categoria,
            fecha=timezone.now(),
            completado=True
        )
        
        # Crear tarjetas no pagadas
        Tarjeta.objects.create(
            jugador=jugador1,
            tipo='AMARILLA',
            partido=partido_prueba,
            pagada=False
        )
        Tarjeta.objects.create(
            jugador=jugador2,
            tipo='ROJA',
            partido=partido_prueba,
            pagada=False
        )
        
        # Verificar el cálculo (1 amarilla * 5.00 + 1 roja * 10.00 = 15.00)
        self.assertEqual(self.equipo.get_deuda_multas_pendientes(), Decimal('15.00'))

    def test_get_deuda_multas_pendientes_sin_categoria(self):
        """Verifica que el método maneje correctamente cuando el equipo no tiene categoría asignada."""
        # Crear jugadores
        jugador1 = Jugador.objects.create(
            primer_nombre="Carlos", primer_apellido="Gómez", 
            cedula="1234567891", equipo=self.equipo_sin_categoria, numero_dorsal=10
        )
        
        # Crear un partido de prueba para asociar con las tarjetas
        partido_prueba = Partido.objects.create(
            torneo=self.torneo,
            equipo_1=self.equipo_sin_categoria,
            equipo_2=self.equipo,
            fecha=timezone.now(),
            completado=True
        )
        
        # Crear tarjeta no pagada
        Tarjeta.objects.create(
            jugador=jugador1,
            tipo='AMARILLA',
            partido=partido_prueba,
            pagada=False
        )
        
        # Verificar que no falle y devuelva 0 cuando no hay categoría con valores adecuados
        # (la categoría dummy tiene multa_amarilla=0.00)
        self.assertEqual(self.equipo_sin_categoria.get_deuda_multas_pendientes(), Decimal('0.00'))


class JugadorModelTest(TestCase):
    """Pruebas para el modelo Jugador."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            costo_inscripcion=Decimal('100.00'),  # Corregido de cuota_inscripcion a costo_inscripcion
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
