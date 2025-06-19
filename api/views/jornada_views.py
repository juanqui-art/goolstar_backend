"""
Vistas relacionadas con la gestión de Jornadas en el sistema.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Jornada, Partido
from api.serializers import JornadaSerializer, PartidoSerializer
from api.utils.logging_utils import get_logger, log_api_request
from api.utils.tz_logging import detect_naive_datetime

logger = get_logger(__name__)

class JornadaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las Jornadas de los torneos.
    
    Una jornada agrupa varios partidos dentro de un torneo.
    """
    queryset = Jornada.objects.all()
    serializer_class = JornadaSerializer
    ordering = ['numero']  # Orden por defecto: por número de jornada
    permission_classes = [IsAuthenticatedOrReadOnly]

    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todas las jornadas (con logging)"""
        logger.info(f"Listando jornadas - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene una jornada específica (con logging)"""
        logger.info(f"Obteniendo detalle de la jornada {kwargs.get('pk')} - Usuario: {request.user}")
        return super().retrieve(request, *args, **kwargs)

    @log_api_request(logger)
    @action(detail=True, methods=['get'])
    def partidos(self, request, pk=None):
        """
        Obtener los partidos de una jornada específica.
        
        Retorna:
        - Lista de partidos de la jornada ordenados por fecha.
        """
        logger.info(f"Buscando partidos para la jornada ID: {pk} - Usuario: {request.user}")
        
        jornada = self.get_object()
        partidos = Partido.objects.filter(jornada=jornada).select_related(
            'equipo_1', 'equipo_2', 'jornada', 'torneo'
        ).order_by('fecha')
        
        # Verificar integridad de fechas
        for partido in partidos:
            # Detectar fechas sin zona horaria
            detect_naive_datetime(partido.fecha, logger)
        
        serializer = PartidoSerializer(partidos, many=True)
        logger.info(f"Partidos encontrados para jornada {pk}: {partidos.count()}")
        
        return Response(serializer.data)
