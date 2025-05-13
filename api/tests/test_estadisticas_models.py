"""
Pruebas para los modelos de estadísticas del sistema GoolStar.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from api.models.base import Categoria, Torneo, FaseEliminatoria
from api.models.participantes import Equipo
from api.models.competicion import Partido
from api.models.estadisticas import EstadisticaEquipo, LlaveEliminatoria, MejorPerdedor, EventoTorneo


class EstadisticaEquipoModelTest(TestCase):
    """Pruebas para el modelo EstadisticaEquipo."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES")
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        
        # Crear equipos para las pruebas
        self.equipo1 = Equipo.objects.create(nombre="Equipo 1", categoria=self.categoria, torneo=self.torneo)
        self.equipo2 = Equipo.objects.create(nombre="Equipo 2", categoria=self.categoria, torneo=self.torneo)
        
        # Crear estadísticas iniciales
        self.estadistica1 = EstadisticaEquipo.objects.create(
            equipo=self.equipo1,
            torneo=self.torneo,
            partidos_jugados=0,
            partidos_ganados=0,
            partidos_empatados=0,
            partidos_perdidos=0,
            goles_favor=0,
            goles_contra=0,
            puntos=0,
            diferencia_goles=0,
            tarjetas_amarillas=0,
            tarjetas_rojas=0
        )
        
        self.estadistica2 = EstadisticaEquipo.objects.create(
            equipo=self.equipo2,
            torneo=self.torneo,
            partidos_jugados=0,
            partidos_ganados=0,
            partidos_empatados=0,
            partidos_perdidos=0,
            goles_favor=0,
            goles_contra=0,
            puntos=0,
            diferencia_goles=0,
            tarjetas_amarillas=0,
            tarjetas_rojas=0
        )

    def test_estadistica_equipo_creation(self):
        """Verifica que la estadística de equipo se crea correctamente."""
        self.assertEqual(self.estadistica1.equipo, self.equipo1)
        self.assertEqual(self.estadistica1.torneo, self.torneo)
        self.assertEqual(self.estadistica1.partidos_jugados, 0)
        self.assertEqual(self.estadistica1.partidos_ganados, 0)
        self.assertEqual(self.estadistica1.partidos_empatados, 0)
        self.assertEqual(self.estadistica1.partidos_perdidos, 0)
        self.assertEqual(self.estadistica1.goles_favor, 0)
        self.assertEqual(self.estadistica1.goles_contra, 0)
        self.assertEqual(self.estadistica1.puntos, 0)
        self.assertEqual(self.estadistica1.diferencia_goles, 0)
        self.assertEqual(self.estadistica1.tarjetas_amarillas, 0)
        self.assertEqual(self.estadistica1.tarjetas_rojas, 0)

    def test_estadistica_equipo_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.estadistica1), f"Estadísticas de {self.equipo1.nombre}")

    def test_actualizar_estadisticas_sin_partidos(self):
        """Verifica que el método actualizar_estadisticas funcione correctamente sin partidos."""
        # Reiniciar estadísticas
        self.estadistica1.partidos_jugados = 0
        self.estadistica1.partidos_ganados = 0
        self.estadistica1.partidos_empatados = 0
        self.estadistica1.partidos_perdidos = 0
        self.estadistica1.goles_favor = 0
        self.estadistica1.goles_contra = 0
        self.estadistica1.diferencia_goles = 0
        self.estadistica1.puntos = 0
        self.estadistica1.save()
        
        # Actualizar estadísticas (no debería cambiar nada sin partidos)
        self.estadistica1.actualizar_estadisticas()
        
        self.assertEqual(self.estadistica1.partidos_jugados, 0)
        self.assertEqual(self.estadistica1.partidos_ganados, 0)
        self.assertEqual(self.estadistica1.puntos, 0)

    def test_actualizar_estadisticas_optimizado(self):
        """Verifica que el método optimizado de actualizar_estadisticas funcione correctamente."""
        # Crear un partido completado donde equipo1 gana
        partido1 = Partido.objects.create(
            torneo=self.torneo,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2,
            fecha=timezone.now(),
            goles_equipo_1=3,
            goles_equipo_2=1,
            completado=True
        )
        
        # Llamar al método optimizado
        self.estadistica1.actualizar_estadisticas()
        self.estadistica2.actualizar_estadisticas()
        
        # Refrescar desde la base de datos
        self.estadistica1.refresh_from_db()
        self.estadistica2.refresh_from_db()
        
        # Verificar estadísticas del equipo 1 (ganador)
        self.assertEqual(self.estadistica1.partidos_jugados, 1)
        self.assertEqual(self.estadistica1.partidos_ganados, 1)
        self.assertEqual(self.estadistica1.partidos_empatados, 0)
        self.assertEqual(self.estadistica1.partidos_perdidos, 0)
        self.assertEqual(self.estadistica1.goles_favor, 3)
        self.assertEqual(self.estadistica1.goles_contra, 1)
        self.assertEqual(self.estadistica1.puntos, 3)  # 3 puntos por victoria
        self.assertEqual(self.estadistica1.diferencia_goles, 2)  # 3 - 1 = 2
        
        # Verificar estadísticas del equipo 2 (perdedor)
        self.assertEqual(self.estadistica2.partidos_jugados, 1)
        self.assertEqual(self.estadistica2.partidos_ganados, 0)
        self.assertEqual(self.estadistica2.partidos_empatados, 0)
        self.assertEqual(self.estadistica2.partidos_perdidos, 1)
        self.assertEqual(self.estadistica2.goles_favor, 1)
        self.assertEqual(self.estadistica2.goles_contra, 3)
        self.assertEqual(self.estadistica2.puntos, 0)  # 0 puntos por derrota
        self.assertEqual(self.estadistica2.diferencia_goles, -2)  # 1 - 3 = -2
        
    def test_actualizar_estadisticas_multiple_partidos(self):
        """Verifica que las estadísticas se actualicen correctamente con múltiples partidos."""
        # Crear varios partidos con diferentes resultados
        
        # Partido 1: Equipo 1 gana
        partido1 = Partido.objects.create(
            torneo=self.torneo,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2,
            fecha=timezone.now() - timedelta(days=10),
            goles_equipo_1=2,
            goles_equipo_2=0,
            completado=True
        )
        
        # Partido 2: Empate
        partido2 = Partido.objects.create(
            torneo=self.torneo,
            equipo_1=self.equipo2,
            equipo_2=self.equipo1,
            fecha=timezone.now() - timedelta(days=5),
            goles_equipo_1=1,
            goles_equipo_2=1,
            completado=True
        )
        
        # Partido 3: Equipo 2 gana
        partido3 = Partido.objects.create(
            torneo=self.torneo,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2,
            fecha=timezone.now(),
            goles_equipo_1=0,
            goles_equipo_2=3,
            completado=True
        )
        
        # Actualizar estadísticas
        self.estadistica1.actualizar_estadisticas()
        self.estadistica2.actualizar_estadisticas()
        
        # Refrescar desde la base de datos
        self.estadistica1.refresh_from_db()
        self.estadistica2.refresh_from_db()
        
        # Verificar estadísticas del equipo 1
        self.assertEqual(self.estadistica1.partidos_jugados, 3)
        self.assertEqual(self.estadistica1.partidos_ganados, 1)
        self.assertEqual(self.estadistica1.partidos_empatados, 1)
        self.assertEqual(self.estadistica1.partidos_perdidos, 1)
        self.assertEqual(self.estadistica1.goles_favor, 3)  # 2 + 1 + 0 = 3
        self.assertEqual(self.estadistica1.goles_contra, 4)  # 0 + 1 + 3 = 4
        self.assertEqual(self.estadistica1.puntos, 4)  # 3 (victoria) + 1 (empate) = 4
        self.assertEqual(self.estadistica1.diferencia_goles, -1)  # 3 - 4 = -1
        
        # Verificar estadísticas del equipo 2
        self.assertEqual(self.estadistica2.partidos_jugados, 3)
        self.assertEqual(self.estadistica2.partidos_ganados, 1)
        self.assertEqual(self.estadistica2.partidos_empatados, 1)
        self.assertEqual(self.estadistica2.partidos_perdidos, 1)
        self.assertEqual(self.estadistica2.goles_favor, 4)  # 0 + 1 + 3 = 4
        self.assertEqual(self.estadistica2.goles_contra, 3)  # 2 + 1 + 0 = 3
        self.assertEqual(self.estadistica2.puntos, 4)  # 0 (derrota) + 1 (empate) + 3 (victoria) = 4
        self.assertEqual(self.estadistica2.diferencia_goles, 1)  # 4 - 3 = 1


class LlaveEliminatoriaModelTest(TestCase):
    """Pruebas para el modelo LlaveEliminatoria."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES")
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        
        self.fase = FaseEliminatoria.objects.create(
            torneo=self.torneo,
            nombre="Cuartos de Final",
            orden=1
        )
        
        self.equipo1 = Equipo.objects.create(nombre="Equipo 1", categoria=self.categoria, torneo=self.torneo)
        self.equipo2 = Equipo.objects.create(nombre="Equipo 2", categoria=self.categoria, torneo=self.torneo)
        
        self.llave = LlaveEliminatoria.objects.create(
            fase=self.fase,
            numero_llave=1,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2
        )

    def test_llave_eliminatoria_creation(self):
        """Verifica que la llave eliminatoria se crea correctamente."""
        self.assertEqual(self.llave.fase, self.fase)
        self.assertEqual(self.llave.numero_llave, 1)
        self.assertEqual(self.llave.equipo_1, self.equipo1)
        self.assertEqual(self.llave.equipo_2, self.equipo2)
        self.assertIsNone(self.llave.partido)
        self.assertFalse(self.llave.completada)

    def test_llave_eliminatoria_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.llave), "Cuartos de Final - Llave 1")

    def test_generar_partido(self):
        """Verifica que el método generar_partido funcione correctamente."""
        self.assertIsNone(self.llave.partido)
        
        # Generar el partido
        self.llave.generar_partido()
        
        # Verificar que se creó el partido
        self.assertIsNotNone(self.llave.partido)
        self.assertEqual(self.llave.partido.torneo, self.torneo)
        self.assertEqual(self.llave.partido.fase_eliminatoria, self.fase)
        self.assertEqual(self.llave.partido.equipo_1, self.equipo1)
        self.assertEqual(self.llave.partido.equipo_2, self.equipo2)
        self.assertTrue(self.llave.partido.es_eliminatorio)

    def test_ganador_sin_partido(self):
        """Verifica que el método ganador funcione correctamente sin partido."""
        self.assertIsNone(self.llave.ganador)

    def test_ganador_con_partido_no_completado(self):
        """Verifica que el método ganador funcione correctamente con partido no completado."""
        self.llave.generar_partido()
        self.assertIsNone(self.llave.ganador)

    def test_ganador_con_partido_completado(self):
        """Verifica que el método ganador funcione correctamente con partido completado."""
        self.llave.generar_partido()
        
        # Completar el partido con victoria del equipo 1
        self.llave.partido.completado = True
        self.llave.partido.goles_equipo_1 = 2
        self.llave.partido.goles_equipo_2 = 1
        self.llave.partido.save()
        
        self.assertEqual(self.llave.ganador, self.equipo1)
        
        # Cambiar el resultado para victoria del equipo 2
        self.llave.partido.goles_equipo_1 = 1
        self.llave.partido.goles_equipo_2 = 2
        self.llave.partido.save()
        
        self.assertEqual(self.llave.ganador, self.equipo2)


class MejorPerdedorModelTest(TestCase):
    """Pruebas para el modelo MejorPerdedor."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES")
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        self.equipo = Equipo.objects.create(nombre="Equipo", categoria=self.categoria, torneo=self.torneo)
        
        self.mejor_perdedor = MejorPerdedor.objects.create(
            torneo=self.torneo,
            grupo="A",
            equipo=self.equipo,
            puntos=4,
            diferencia_goles=1,
            goles_contra=5,
            goles_favor=6
        )

    def test_mejor_perdedor_creation(self):
        """Verifica que el mejor perdedor se crea correctamente."""
        self.assertEqual(self.mejor_perdedor.torneo, self.torneo)
        self.assertEqual(self.mejor_perdedor.grupo, "A")
        self.assertEqual(self.mejor_perdedor.equipo, self.equipo)
        self.assertEqual(self.mejor_perdedor.puntos, 4)
        self.assertEqual(self.mejor_perdedor.diferencia_goles, 1)
        self.assertEqual(self.mejor_perdedor.goles_contra, 5)
        self.assertEqual(self.mejor_perdedor.goles_favor, 6)


class EventoTorneoModelTest(TestCase):
    """Pruebas para el modelo EventoTorneo."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        self.categoria = Categoria.objects.create(nombre="VARONES")
        self.torneo = Torneo.objects.create(nombre="Torneo", categoria=self.categoria, fecha_inicio=timezone.now().date())
        self.equipo = Equipo.objects.create(nombre="Equipo", categoria=self.categoria, torneo=self.torneo)
        
        self.evento = EventoTorneo.objects.create(
            torneo=self.torneo,
            tipo=EventoTorneo.TipoEvento.INICIO_GRUPOS,
            descripcion="Inicio de la fase de grupos",
            equipo_involucrado=None,
            datos_adicionales={"grupos": 2}
        )
        
        self.evento_equipo = EventoTorneo.objects.create(
            torneo=self.torneo,
            tipo=EventoTorneo.TipoEvento.EXCLUSION_EQUIPO,
            descripcion="Equipo excluido por inasistencias",
            equipo_involucrado=self.equipo,
            datos_adicionales={"inasistencias": 3}
        )

    def test_evento_torneo_creation(self):
        """Verifica que el evento de torneo se crea correctamente."""
        self.assertEqual(self.evento.torneo, self.torneo)
        self.assertEqual(self.evento.tipo, "inicio_grupos")
        self.assertEqual(self.evento.descripcion, "Inicio de la fase de grupos")
        self.assertIsNone(self.evento.equipo_involucrado)
        self.assertEqual(self.evento.datos_adicionales, {"grupos": 2})

    def test_evento_torneo_con_equipo(self):
        """Verifica que el evento de torneo con equipo se crea correctamente."""
        self.assertEqual(self.evento_equipo.torneo, self.torneo)
        self.assertEqual(self.evento_equipo.tipo, "exclusion")
        self.assertEqual(self.evento_equipo.equipo_involucrado, self.equipo)
        self.assertEqual(self.evento_equipo.datos_adicionales, {"inasistencias": 3})

    def test_evento_torneo_str(self):
        """Verifica que el método __str__ funcione correctamente."""
        self.assertEqual(str(self.evento), "Torneo - Inicio Fase de Grupos")
