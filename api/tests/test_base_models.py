"""
Pruebas para los modelos base del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from api.models.base import Nivel, Categoria, Torneo, FaseEliminatoria


class NivelModelTest(TestCase):
    """Pruebas para el modelo Nivel."""

    def test_nivel_choices(self):
        """Verifica que las opciones de nivel estén correctamente definidas."""
        self.assertEqual(Nivel.MUY_BAJO, 1)
        self.assertEqual(Nivel.BAJO, 2)
        self.assertEqual(Nivel.MEDIO, 3)
        self.assertEqual(Nivel.ALTO, 4)
        self.assertEqual(Nivel.MUY_ALTO, 5)


class CategoriaModelTest(TestCase):
    """Pruebas para el modelo Categoria."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            descripcion="Categoría para equipos masculinos",
            premio_primero=1000.00,
            premio_segundo=500.00,
            premio_tercero=300.00,
            costo_inscripcion=100.00,
            costo_arbitraje=10.00,
            multa_amarilla=2.00,
            multa_roja=5.00,
            limite_inasistencias=3,
            limite_amarillas_suspension=3,
            partidos_suspension_roja=2
        )

    def test_categoria_creation(self):
        """Verifica que la categoría se crea correctamente."""
        self.assertEqual(self.categoria.nombre, "VARONES")
        self.assertEqual(self.categoria.premio_primero, 1000.00)
        self.assertEqual(self.categoria.costo_inscripcion, 100.00)
        self.assertEqual(self.categoria.multa_amarilla, 2.00)
        self.assertEqual(self.categoria.multa_roja, 5.00)

    def test_categoria_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.categoria), "VARONES")


class TorneoModelTest(TestCase):
    """Pruebas para el modelo Torneo."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            costo_inscripcion=100.00
        )
        
        self.torneo = Torneo.objects.create(
            nombre="Torneo Apertura 2025",
            categoria=self.categoria,
            fecha_inicio=timezone.now().date(),
            fecha_fin=timezone.now().date() + timedelta(days=90),
            activo=True,
            tiene_fase_grupos=True,
            numero_grupos=2,
            equipos_clasifican_por_grupo=2
        )

    def test_torneo_creation(self):
        """Verifica que el torneo se crea correctamente."""
        self.assertEqual(self.torneo.nombre, "Torneo Apertura 2025")
        self.assertEqual(self.torneo.categoria, self.categoria)
        self.assertTrue(self.torneo.activo)
        self.assertFalse(self.torneo.finalizado)
        self.assertTrue(self.torneo.tiene_fase_grupos)
        self.assertEqual(self.torneo.numero_grupos, 2)
        self.assertEqual(self.torneo.fase_actual, "inscripcion")

    def test_torneo_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.torneo), "Torneo Apertura 2025 - VARONES")


class FaseEliminatoriaModelTest(TestCase):
    """Pruebas para el modelo FaseEliminatoria."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(
            nombre="VARONES",
            costo_inscripcion=100.00
        )
        
        self.torneo = Torneo.objects.create(
            nombre="Torneo Apertura 2025",
            categoria=self.categoria,
            fecha_inicio=timezone.now().date(),
            tiene_fase_grupos=True,
            tiene_eliminacion_directa=True
        )
        
        self.fase = FaseEliminatoria.objects.create(
            torneo=self.torneo,
            nombre="Cuartos de Final",
            orden=1,
            fecha_inicio=timezone.now().date() + timedelta(days=60)
        )

    def test_fase_eliminatoria_creation(self):
        """Verifica que la fase eliminatoria se crea correctamente."""
        self.assertEqual(self.fase.nombre, "Cuartos de Final")
        self.assertEqual(self.fase.torneo, self.torneo)
        self.assertEqual(self.fase.orden, 1)
        self.assertFalse(self.fase.completada)

    def test_fase_eliminatoria_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.fase), "Torneo Apertura 2025 - VARONES - Cuartos de Final")

    def test_partidos_pendientes(self):
        """Verifica que el método partidos_pendientes funcione correctamente."""
        # Inicialmente no hay partidos
        self.assertEqual(self.fase.partidos_pendientes, 0)

    def test_puede_iniciar_siguiente_fase(self):
        """Verifica que el método puede_iniciar_siguiente_fase funcione correctamente."""
        # Sin partidos pendientes, debería poder iniciar la siguiente fase
        self.assertTrue(self.fase.puede_iniciar_siguiente_fase)
        
        # Si la fase está completada, también debería poder iniciar la siguiente
        self.fase.completada = True
        self.fase.save()
        self.assertTrue(self.fase.puede_iniciar_siguiente_fase)
