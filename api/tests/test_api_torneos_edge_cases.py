"""
Tests para casos borde en la API de Torneos.
"""

from datetime import date, timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from api.models.base import Torneo, Categoria
from api.models.participantes import Equipo


class TorneoAPIEdgeCaseTests(APITestCase):
    """
    Pruebas para casos borde en los endpoints de la API de Torneos.
    """

    def setUp(self):
        """Configuración inicial para las pruebas."""
        # Crear categoría para las pruebas
        self.categoria = Categoria.objects.create(
            nombre='Varones', 
            descripcion='Categoría masculina'
        )
        
        # Fechas para los torneos
        today = date.today()
        
        # Crear un torneo vacío (sin equipos)
        self.torneo_vacio = Torneo.objects.create(
            nombre='Torneo Vacío',
            categoria=self.categoria,
            fecha_inicio=today,
            activo=True,
            finalizado=False
        )
        
        # Crear un torneo con equipos pero sin partidos
        self.torneo_sin_partidos = Torneo.objects.create(
            nombre='Torneo Sin Partidos',
            categoria=self.categoria,
            fecha_inicio=today - timedelta(days=10),
            activo=True,
            finalizado=False
        )
        
        # Crear equipos para el torneo sin partidos
        self.equipo1 = Equipo.objects.create(
            nombre='Equipo A',
            categoria=self.categoria,
            grupo='A',
            torneo=self.torneo_sin_partidos
        )
        
        self.equipo2 = Equipo.objects.create(
            nombre='Equipo B',
            categoria=self.categoria,
            grupo='A',
            torneo=self.torneo_sin_partidos
        )

    def test_torneo_vacio_estadisticas(self):
        """
        Prueba que la API maneje correctamente un torneo sin equipos ni partidos
        al solicitar estadísticas.
        """
        url = reverse('torneo-estadisticas', args=[self.torneo_vacio.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar valores por defecto para torneo vacío
        estadisticas = response.data['estadisticas_generales']
        self.assertEqual(estadisticas['total_equipos'], 0)
        self.assertEqual(estadisticas['total_partidos'], 0)
        self.assertEqual(estadisticas['partidos_jugados'], 0)
        self.assertEqual(estadisticas['total_goles'], 0)
        self.assertEqual(estadisticas['promedio_goles_por_partido'], 0)
        
        # Verificar que no hay mejores equipos
        mejores_equipos = response.data['mejores_equipos']
        self.assertIsNone(mejores_equipos['equipo_mas_goleador']['nombre'])
        self.assertIsNone(mejores_equipos['equipo_menos_goleado']['nombre'])

    def test_torneo_sin_partidos_tabla_posiciones(self):
        """
        Prueba que la API maneje correctamente un torneo con equipos pero sin partidos
        al solicitar la tabla de posiciones.
        """
        url = reverse('torneo-tabla-posiciones', args=[self.torneo_sin_partidos.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la estructura es correcta pero no hay datos de estadísticas
        self.assertIn('grupo', response.data)
        self.assertIn('equipos', response.data)
        self.assertEqual(len(response.data['equipos']), 0)  # No hay estadísticas aún

    def test_torneo_no_existe(self):
        """
        Prueba que la API maneje correctamente la solicitud de un torneo que no existe.
        """
        # ID que no existe en la base de datos
        torneo_id_inexistente = 9999
        
        # Intentar obtener detalles de un torneo inexistente
        url = reverse('torneo-detail', args=[torneo_id_inexistente])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Intentar obtener tabla de posiciones de un torneo inexistente
        url = reverse('torneo-tabla-posiciones', args=[torneo_id_inexistente])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Intentar obtener estadísticas de un torneo inexistente
        url = reverse('torneo-estadisticas', args=[torneo_id_inexistente])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_crear_torneo_datos_invalidos(self):
        """
        Prueba que la API maneje correctamente la creación de un torneo con datos inválidos.
        """
        url = reverse('torneo-list')
        
        # Intentar crear un torneo sin nombre
        data = {
            'categoria': self.categoria.id,
            'fecha_inicio': date.today().strftime('%Y-%m-%d'),
            'activo': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Intentar crear un torneo sin categoría
        data = {
            'nombre': 'Torneo Inválido',
            'fecha_inicio': date.today().strftime('%Y-%m-%d'),
            'activo': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Intentar crear un torneo con fecha de fin anterior a fecha de inicio
        data = {
            'nombre': 'Torneo Fechas Inválidas',
            'categoria': self.categoria.id,
            'fecha_inicio': date.today().strftime('%Y-%m-%d'),
            'fecha_fin': (date.today() - timedelta(days=10)).strftime('%Y-%m-%d'),
            'activo': True
        }
        response = self.client.post(url, data, format='json')
        # Debería fallar, pero depende de si hay validación en el modelo o serializer
        # Este test podría fallar si no hay tal validación implementada aún
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)
