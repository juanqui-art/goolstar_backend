"""
Vistas relacionadas con la gestión de Goles en el sistema.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Gol
from api.serializers import GolSerializer
from api.utils.logging_utils import get_logger, log_api_request

logger = get_logger(__name__)

class GolViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Goles marcados en los partidos.
    
    Un gol es anotado por un jugador en un partido específico.
    """
    queryset = Gol.objects.all().select_related('jugador', 'partido')
    serializer_class = GolSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todos los goles (con logging)"""
        logger.info(f"Listando goles - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un gol específico (con logging)"""
        logger.info(f"Obteniendo detalle del gol {kwargs.get('pk')} - Usuario: {request.user}")
        return super().retrieve(request, *args, **kwargs)

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
        partido_id = request.query_params.get('partido_id')
        logger.info(f"Buscando goles para el partido ID: {partido_id} - Usuario: {request.user}")
        
        if not partido_id:
            logger.warning(f"Solicitud de goles sin especificar partido_id - Usuario: {request.user}")
            return Response({"error": "Debe especificar el parámetro partido_id"}, status=400)
        
        queryset = Gol.objects.filter(partido__id=partido_id).select_related('jugador', 'partido')
        serializer = self.get_serializer(queryset, many=True)
        
        logger.info(f"Goles encontrados para partido ID {partido_id}: {queryset.count()}")
        return Response(serializer.data)
