"""
Tests para los nuevos endpoints de la API: próximos partidos y jugadores destacados.
"""

from datetime import timedelta, date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.base import Torneo, Categoria
from api.models.competicion import Partido, Jornada, Gol, Tarjeta
from api.models.participantes import Equipo, Jugador
from api.utils.date_utils import get_today_date, date_to_datetime


class ProximosPartidosAPITests(APITestCase):
    """
    Pruebas para el endpoint de próximos partidos.
    """

    # Función auxiliar para crear fechas con zona horaria
    def make_aware_date(self, days_delta=0):
        """
        Crea una fecha con zona horaria correcta, evitando el problema de 'naive datetimes'.
        Reemplaza el método anterior que usaba timezone.now().date() directo.
        
        Args:
            days_delta: Número de días a añadir/restar a la fecha actual
            
        Returns:
            Objeto datetime con información de zona horaria (aware)
        """
        # Obtenemos la fecha actual como objeto date
        today_date = get_today_date()

        # Aplicamos el delta de días
        target_date = today_date + timedelta(days=days_delta)

        # Convertimos a datetime aware
        return date_to_datetime(target_date)

    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear categoría para las pruebas
        self.categoria = Categoria.objects.create(
            nombre='Varones',
            descripcion='Categoría masculina'
        )

        # Fechas para los torneos y partidos
        self.today = self.make_aware_date()
        self.today_date = self.today.date()

        # Crear un torneo para las pruebas
        self.torneo = Torneo.objects.create(
            nombre='Torneo de Prueba',
            categoria=self.categoria,
            fecha_inicio=self.make_aware_date(-10).date(),
            activo=True,
            finalizado=False
        )

        # Crear equipos para el torneo
        self.equipo1 = Equipo.objects.create(
            nombre='Equipo A',
            categoria=self.categoria,
            grupo='A',
            torneo=self.torneo
        )

        self.equipo2 = Equipo.objects.create(
            nombre='Equipo B',
            categoria=self.categoria,
            grupo='A',
            torneo=self.torneo
        )

        self.equipo3 = Equipo.objects.create(
            nombre='Equipo C',
            categoria=self.categoria,
            grupo='B',
            torneo=self.torneo
        )

        # Crear jornada para los partidos
        self.jornada = Jornada.objects.create(
            numero=1,
            nombre='Jornada 1'
        )

        # Crear partidos: uno pasado, uno para hoy, y varios para fechas futuras
        # Partido pasado (ya completado)
        self.partido_pasado = Partido.objects.create(
            jornada=self.jornada,
            torneo=self.torneo,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2,
            fecha=self.make_aware_date(-5),
            completado=True,
            goles_equipo_1=2,
            goles_equipo_2=1
        )

        # Partido para hoy (no completado)
        self.partido_hoy = Partido.objects.create(
            jornada=self.jornada,
            torneo=self.torneo,
            equipo_1=self.equipo2,
            equipo_2=self.equipo3,
            fecha=self.make_aware_date(),
            completado=False
        )

        # Partido futuro (a 3 días)
        self.partido_futuro_1 = Partido.objects.create(
            jornada=self.jornada,
            torneo=self.torneo,
            equipo_1=self.equipo1,
            equipo_2=self.equipo3,
            fecha=self.make_aware_date(3),
            completado=False
        )

        # Partido futuro (a 6 días)
        self.partido_futuro_2 = Partido.objects.create(
            jornada=self.jornada,
            torneo=self.torneo,
            equipo_1=self.equipo3,
            equipo_2=self.equipo1,
            fecha=self.make_aware_date(6),
            completado=False
        )

        # Partido muy futuro (fuera del rango predeterminado de 7 días)
        self.partido_futuro_3 = Partido.objects.create(
            jornada=self.jornada,
            torneo=self.torneo,
            equipo_1=self.equipo2,
            equipo_2=self.equipo1,
            fecha=self.make_aware_date(10),
            completado=False
        )

    def test_proximos_partidos_default(self):
        """Prueba para listar próximos partidos con parámetros predeterminados."""
        url = reverse('partido-proximos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura de la respuesta
        self.assertIn('periodo', response.data)
        self.assertIn('total_partidos', response.data)
        self.assertIn('partidos', response.data)

        # Verificar que solo se incluyen partidos no completados en fecha futura o actual
        # Debe incluir partido_hoy, partido_futuro_1 y partido_futuro_2 (3 en total)
        self.assertEqual(response.data['total_partidos'], 3)

        # Verificar que el partido pasado no está incluido
        partidos_ids = [p['id'] for p in response.data['partidos']]
        self.assertNotIn(self.partido_pasado.id, partidos_ids)

        # Verificar que el partido muy futuro no está incluido (por defecto 7 días)
        self.assertNotIn(self.partido_futuro_3.id, partidos_ids)

    def test_proximos_partidos_filtro_torneo(self):
        """Prueba para filtrar próximos partidos por torneo."""
        url = f"{reverse('partido-proximos')}?torneo_id={self.torneo.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Debe tener los mismos resultados que el test anterior ya que todos pertenecen al mismo torneo
        self.assertEqual(response.data['total_partidos'], 3)

    def test_proximos_partidos_filtro_equipo(self):
        """Prueba para filtrar próximos partidos por equipo."""
        url = f"{reverse('partido-proximos')}?equipo_id={self.equipo1.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Solo debería incluir partidos del equipo1 (partido_futuro_1 y partido_futuro_2)
        self.assertEqual(response.data['total_partidos'], 2)

        # Verificar que solo incluye partidos donde participa equipo1
        for partido in response.data['partidos']:
            self.assertTrue(
                partido['equipo_1']['id'] == self.equipo1.id or
                partido['equipo_2']['id'] == self.equipo1.id
            )

    def test_proximos_partidos_dias_personalizados(self):
        """Prueba para personalizar el número de días hacia adelante."""
        # Solicitar con 15 días hacia adelante (debería incluir todos los partidos futuros)
        url = f"{reverse('partido-proximos')}?dias=15"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Debe incluir todos los partidos futuros (4 en total)
        self.assertEqual(response.data['total_partidos'], 4)

        # Verificar que el partido muy futuro está incluido
        partidos_ids = [p['id'] for p in response.data['partidos']]
        self.assertIn(self.partido_futuro_3.id, partidos_ids)

    def test_proximos_partidos_parametro_invalido(self):
        """Prueba para manejar un parámetro 'dias' inválido."""
        url = f"{reverse('partido-proximos')}?dias=texto_invalido"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Debería usar el valor predeterminado (7 días)
        # por lo que debería excluir partido_futuro_3
        partidos_ids = [p['id'] for p in response.data['partidos']]
        self.assertNotIn(self.partido_futuro_3.id, partidos_ids)


class JugadoresDestacadosAPITests(APITestCase):
    """
    Pruebas para el endpoint de jugadores destacados por torneo.
    """

    # Función auxiliar para crear fechas con zona horaria
    def make_aware_date(self, days_delta=0):
        """
        Crea una fecha con zona horaria correcta, evitando el problema de 'naive datetimes'.
        Reemplaza el método anterior que usaba timezone.now().date() directo.
        
        Args:
            days_delta: Número de días a añadir/restar a la fecha actual
            
        Returns:
            Objeto datetime con información de zona horaria (aware)
        """
        # Obtenemos la fecha actual como objeto date
        today_date = get_today_date()

        # Aplicamos el delta de días
        target_date = today_date + timedelta(days=days_delta)

        # Convertimos a datetime aware
        return date_to_datetime(target_date)

    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear categoría para las pruebas
        self.categoria = Categoria.objects.create(
            nombre='Varones',
            descripcion='Categoría masculina'
        )

        # Fechas para los torneos y partidos
        self.today = self.make_aware_date()
        self.today_date = self.today.date()

        # Crear un torneo para las pruebas
        self.torneo = Torneo.objects.create(
            nombre='Torneo de Prueba',
            categoria=self.categoria,
            fecha_inicio=self.make_aware_date(-30).date(),
            activo=True,
            finalizado=False
        )

        # Crear equipos para el torneo
        self.equipo1 = Equipo.objects.create(
            nombre='Equipo A',
            categoria=self.categoria,
            grupo='A',
            torneo=self.torneo
        )

        self.equipo2 = Equipo.objects.create(
            nombre='Equipo B',
            categoria=self.categoria,
            grupo='A',
            torneo=self.torneo
        )

        # Crear jornada para los partidos
        self.jornada = Jornada.objects.create(
            numero=1,
            nombre='Jornada 1'
        )

        # Crear partido para las estadísticas
        self.partido = Partido.objects.create(
            jornada=self.jornada,
            torneo=self.torneo,
            equipo_1=self.equipo1,
            equipo_2=self.equipo2,
            fecha=self.make_aware_date(-15),
            completado=True,
            goles_equipo_1=3,
            goles_equipo_2=1
        )

        # Crear jugadores
        self.jugador1 = Jugador.objects.create(
            primer_nombre='Juan',
            primer_apellido='Pérez',
            equipo=self.equipo1,
            cedula='1234567890',
            fecha_nacimiento=date(1998, 5, 15)
        )

        self.jugador2 = Jugador.objects.create(
            primer_nombre='Carlos',
            primer_apellido='López',
            equipo=self.equipo1,
            cedula='2345678901',
            fecha_nacimiento=date(1997, 8, 21)
        )

        self.jugador3 = Jugador.objects.create(
            primer_nombre='Luis',
            primer_apellido='González',
            equipo=self.equipo2,
            cedula='3456789012',
            fecha_nacimiento=date(1999, 3, 10)
        )

        # Crear goles
        # Jugador 1: 2 goles
        Gol.objects.create(
            partido=self.partido,
            jugador=self.jugador1,
            minuto=15
        )

        Gol.objects.create(
            partido=self.partido,
            jugador=self.jugador1,
            minuto=45
        )

        # Jugador 2: 1 gol
        Gol.objects.create(
            partido=self.partido,
            jugador=self.jugador2,
            minuto=70
        )

        # Jugador 3: 1 gol
        Gol.objects.create(
            partido=self.partido,
            jugador=self.jugador3,
            minuto=80
        )

        # Crear tarjetas
        # Jugador 1: 1 amarilla
        Tarjeta.objects.create(
            partido=self.partido,
            jugador=self.jugador1,
            tipo='AMARILLA',
            minuto=30
        )

        # Jugador 3: 2 amarillas y 1 roja
        Tarjeta.objects.create(
            partido=self.partido,
            jugador=self.jugador3,
            tipo='AMARILLA',
            minuto=40
        )

        Tarjeta.objects.create(
            partido=self.partido,
            jugador=self.jugador3,
            tipo='AMARILLA',
            minuto=60
        )

        Tarjeta.objects.create(
            partido=self.partido,
            jugador=self.jugador3,
            tipo='ROJA',
            minuto=85
        )

    def test_jugadores_destacados(self):
        """Prueba para obtener jugadores destacados del torneo."""
        url = reverse('torneo-jugadores-destacados', args=[self.torneo.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar estructura de la respuesta
        self.assertIn('torneo', response.data)
        self.assertIn('goleadores', response.data)
        self.assertIn('tarjetas_amarillas', response.data)
        self.assertIn('tarjetas_rojas', response.data)

        # Verificar goleadores
        goleadores = response.data['goleadores']
        self.assertEqual(len(goleadores), 3)

        # El primer goleador debe ser el jugador1 con 2 goles
        self.assertEqual(goleadores[0]['goles'], 2)
        self.assertEqual(goleadores[0]['jugador'], 'Juan Pérez')

        # Verificar tarjetas amarillas
        tarjetas_amarillas = response.data['tarjetas_amarillas']
        self.assertEqual(len(tarjetas_amarillas), 2)

        # El jugador3 debe tener 2 amarillas
        self.assertEqual(tarjetas_amarillas[0]['amarillas'], 2)
        self.assertEqual(tarjetas_amarillas[0]['jugador'], 'Luis González')

        # Verificar tarjetas rojas
        tarjetas_rojas = response.data['tarjetas_rojas']
        self.assertEqual(len(tarjetas_rojas), 1)
        self.assertEqual(tarjetas_rojas[0]['rojas'], 1)
        self.assertEqual(tarjetas_rojas[0]['jugador'], 'Luis González')

    def test_jugadores_destacados_limite_personalizado(self):
        """Prueba para personalizar el límite de jugadores destacados."""
        url = f"{reverse('torneo-jugadores-destacados', args=[self.torneo.id])}?limite=1"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que solo se muestra 1 jugador en cada categoría
        self.assertEqual(len(response.data['goleadores']), 1)
        self.assertEqual(len(response.data['tarjetas_amarillas']), 1)
        self.assertEqual(len(response.data['tarjetas_rojas']), 1)

    def test_jugadores_destacados_torneo_vacio(self):
        """Prueba para un torneo sin jugadores destacados."""
        # Crear un torneo vacío
        torneo_vacio = Torneo.objects.create(
            nombre='Torneo Vacío',
            categoria=self.categoria,
            fecha_inicio=self.make_aware_date().date(),
            activo=True,
            finalizado=False
        )

        url = reverse('torneo-jugadores-destacados', args=[torneo_vacio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verificar que las listas están vacías
        self.assertEqual(len(response.data['goleadores']), 0)
        self.assertEqual(len(response.data['tarjetas_amarillas']), 0)
        self.assertEqual(len(response.data['tarjetas_rojas']), 0)

    def test_jugadores_destacados_parametro_invalido(self):
        """Prueba para manejar un parámetro 'limite' inválido."""
        url = f"{reverse('torneo-jugadores-destacados', args=[self.torneo.id])}?limite=texto_invalido"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Debería usar el valor predeterminado (5)
        # Como solo tenemos 3 jugadores en total, deberían mostrarse todos
        self.assertEqual(len(response.data['goleadores']), 3)
