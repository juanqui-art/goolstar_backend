"""
Vistas relacionadas con la gestión de Jugadores en el sistema.
"""
from django.db.models import Count
from django.db.models import Q
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.models import Jugador
from api.serializers import JugadorSerializer, JugadorListSerializer
# Ya existe PageNumberPagination importado arriba
from api.utils.date_utils import get_today_date
from api.utils.logging_utils import get_logger, log_api_request

logger = get_logger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 1000


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
    ordering = ['primer_apellido', 'primer_nombre']  # Orden por defecto para evitar UnorderedObjectListWarning
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return JugadorListSerializer
        return JugadorSerializer

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
        - Soporta paginación a través de los parámetros estándar de DRF (page, page_size)
        """
        logger.info(f"Generando listado de goleadores - Usuario: {request.user}")

        # Fecha actual (usando utilidad de zona horaria)
        today = get_today_date()
        logger.debug(f"Fecha actual para filtro de goleadores: {today}")

        # Consulta base con anotación de total_goles
        queryset = Jugador.objects.select_related('equipo').annotate(
            total_goles=Count('goles')
        ).filter(total_goles__gt=0)

        # Aplicar filtros adicionales si es necesario (por ejemplo, por torneo)
        torneo_id = request.query_params.get('torneo')
        if torneo_id:
            queryset = Jugador.objects.select_related('equipo').annotate(
                total_goles=Count('goles', filter=Q(goles__partido__torneo_id=torneo_id))
            ).filter(total_goles__gt=0)

        # Siempre ordenar por total_goles (descendente) y luego por apellido
        queryset = queryset.order_by('-total_goles', 'primer_apellido')

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            data = serializer.data
            # Añadir total_goles a cada jugador en la respuesta
            for i, jugador in enumerate(page):
                data[i]['total_goles'] = jugador.total_goles

            logger.info(f"Goleadores paginados: {len(page)} de {queryset.count()}")
            return self.get_paginated_response(data)

        # Sin paginación (caso fallback)
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        for i, jugador in enumerate(queryset):
            data[i]['total_goles'] = jugador.total_goles

        logger.info(f"Total de goleadores encontrados: {queryset.count()}")
        return Response(data)
