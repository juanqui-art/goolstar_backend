"""
Vistas relacionadas con la gestión de Goles en el sistema.
"""
from rest_framework import viewsets, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.db import transaction
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
import time

from api.models import Gol
from api.serializers import GolSerializer
from api.utils.logging_utils import get_logger, log_api_request

logger = get_logger(__name__)

class GolPagination(pagination.PageNumberPagination):
    """Paginación específica para optimizar el rendimiento de Goles"""
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 100


class GolViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Goles marcados en los partidos.
    
    Un gol es anotado por un jugador en un partido específico.
    """
    queryset = Gol.objects.all().select_related(
        'jugador', 
        'partido', 
        'jugador__equipo', 
        'partido__equipo_1', 
        'partido__equipo_2', 
        'partido__torneo'
    ).order_by('-partido__fecha', 'minuto', 'id')
    serializer_class = GolSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = GolPagination  # Usar paginación específica para mejorar rendimiento

    def get_queryset(self):
        """
        Optimiza la consulta base dependiendo de la acción.
        """
        queryset = super().get_queryset()
        
        # Aplicar filtros según parámetros de consulta
        jugador_id = self.request.query_params.get('jugador_id')
        equipo_id = self.request.query_params.get('equipo_id')
        torneo_id = self.request.query_params.get('torneo_id')
        
        if jugador_id:
            queryset = queryset.filter(jugador_id=jugador_id)
        if equipo_id:
            queryset = queryset.filter(jugador__equipo_id=equipo_id)
        if torneo_id:
            queryset = queryset.filter(partido__torneo_id=torneo_id)
            
        return queryset

    @method_decorator(cache_page(300))  # Aumentar cache a 5 minutos para mejorar rendimiento
    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todos los goles (con logging y métricas de rendimiento)"""
        start_time = time.time()
        logger.info(f"Listando goles - Usuario: {request.user}")
        
        response = super().list(request, *args, **kwargs)
        
        # Registrar métricas de rendimiento
        elapsed_time = time.time() - start_time
        logger.info(f"Rendimiento del listado de goles: {elapsed_time:.2f}s - Items: {self.paginator.page.paginator.count if hasattr(self, 'paginator') and self.paginator else 'N/A'}")
        
        return response
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un gol específico (con logging)"""
        logger.info(f"Obteniendo detalle del gol {kwargs.get('pk')} - Usuario: {request.user}")
        # Intenta obtener de caché primero
        cache_key = f"gol_detail_{kwargs.get('pk')}"
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Recuperando gol {kwargs.get('pk')} desde caché")
            return Response(cached_data)
        
        # Si no está en caché, obtenerlo normalmente
        response = super().retrieve(request, *args, **kwargs)
        
        # Guardar en caché por 5 minutos (aumentado de 2 minutos)
        cache.set(cache_key, response.data, 300)
        return response

    @transaction.atomic
    @log_api_request(logger)
    def create(self, request, *args, **kwargs):
        """Crea un nuevo gol con protección de transacción"""
        logger.info(f"Creando nuevo gol - Usuario: {request.user}")
        response = super().create(request, *args, **kwargs)
        # Invalidar cache relacionado
        cache.delete_pattern("gol_list_*")
        return response

    @transaction.atomic
    @log_api_request(logger)
    def update(self, request, *args, **kwargs):
        """Actualiza un gol con protección de transacción"""
        logger.info(f"Actualizando gol {kwargs.get('pk')} - Usuario: {request.user}")
        response = super().update(request, *args, **kwargs)
        # Invalidar cache específico y listados
        cache.delete(f"gol_detail_{kwargs.get('pk')}")
        cache.delete_pattern("gol_list_*")
        return response

    @transaction.atomic
    @log_api_request(logger)
    def destroy(self, request, *args, **kwargs):
        """Elimina un gol con protección de transacción"""
        logger.info(f"Eliminando gol {kwargs.get('pk')} - Usuario: {request.user}")
        response = super().destroy(request, *args, **kwargs)
        # Invalidar cache relacionado
        cache.delete(f"gol_detail_{kwargs.get('pk')}")
        cache.delete_pattern("gol_list_*")
        return response

    @cache_page(300)  # Aumentar cache a 5 minutos
    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def por_partido(self, request):
        """
        Filtrar goles por partido.
        
        Parámetros:
        - partido_id: ID del partido para filtrar los goles
        
        Retorna:
        - Lista de goles marcados en el partido especificado
        """
        start_time = time.time()
        partido_id = request.query_params.get('partido_id')
        logger.info(f"Buscando goles para el partido ID: {partido_id} - Usuario: {request.user}")
        
        if not partido_id:
            logger.warning(f"Solicitud de goles sin especificar partido_id - Usuario: {request.user}")
            return Response({"error": "Debe especificar el parámetro partido_id"}, status=400)
        
        queryset = Gol.objects.filter(partido__id=partido_id).select_related(
            'jugador', 
            'partido', 
            'jugador__equipo'
        ).order_by('minuto', 'id')
        
        serializer = self.get_serializer(queryset, many=True)
        
        elapsed_time = time.time() - start_time
        logger.info(f"Goles encontrados para partido ID {partido_id}: {queryset.count()} - Tiempo: {elapsed_time:.2f}s")
        return Response(serializer.data)
