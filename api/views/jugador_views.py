"""
Vistas relacionadas con la gestión de Jugadores en el sistema.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Jugador
from api.serializers import JugadorSerializer
from api.utils.logging_utils import get_logger, log_api_request
from api.utils.date_utils import get_today_date

logger = get_logger(__name__)

class JugadorViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Jugadores de los equipos.
    
    Un jugador pertenece a un equipo y tiene estadísticas asociadas.
    """
    queryset = Jugador.objects.all().select_related('equipo')
    serializer_class = JugadorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['primer_nombre', 'primer_apellido', 'cedula']
    ordering_fields = ['primer_apellido', 'primer_nombre']
    permission_classes = [IsAuthenticatedOrReadOnly]

    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todos los jugadores (con logging)"""
        logger.info(f"Listando jugadores - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un jugador específico (con logging)"""
        logger.info(f"Obteniendo detalle del jugador {kwargs.get('pk')} - Usuario: {request.user}")
        return super().retrieve(request, *args, **kwargs)

    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def por_equipo(self, request):
        """
        Filtrar jugadores por equipo.
        
        Parámetros:
        - equipo_id: ID del equipo para filtrar los jugadores
        
        Retorna:
        - Lista de jugadores que pertenecen al equipo especificado
        """
        equipo_id = request.query_params.get('equipo_id')
        logger.info(f"Buscando jugadores para el equipo ID: {equipo_id} - Usuario: {request.user}")
        
        if not equipo_id:
            logger.warning(f"Solicitud de jugadores sin especificar equipo_id - Usuario: {request.user}")
            return Response({"error": "Debe especificar el parámetro equipo_id"}, status=400)
        
        queryset = Jugador.objects.filter(equipo__id=equipo_id).select_related('equipo')
        serializer = self.get_serializer(queryset, many=True)
        
        logger.info(f"Jugadores encontrados para equipo ID {equipo_id}: {queryset.count()}")
        return Response(serializer.data)

    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def goleadores(self, request):
        """
        Obtener lista de jugadores con sus estadísticas de goles.
        
        Retorna:
        - Lista de jugadores ordenados por la cantidad de goles marcados (descendente)
        """
        logger.info(f"Generando listado de goleadores - Usuario: {request.user}")
        
        # Fecha actual (usando utilidad de zona horaria)
        today = get_today_date()
        logger.debug(f"Fecha actual para filtro de goleadores: {today}")
        
        queryset = Jugador.objects.annotate(
            total_goles=Count('gol')
        ).filter(total_goles__gt=0).order_by('-total_goles', 'primer_apellido')
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Total de goleadores encontrados: {queryset.count()}")
        
        return Response(serializer.data)
