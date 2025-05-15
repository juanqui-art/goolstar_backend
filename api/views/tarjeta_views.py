"""
Vistas relacionadas con la gestión de Tarjetas en el sistema.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Tarjeta
from api.serializers import TarjetaSerializer
from api.utils.logging_utils import get_logger, log_api_request

logger = get_logger(__name__)

class TarjetaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las Tarjetas (amarillas y rojas) mostradas en los partidos.
    
    Una tarjeta es mostrada a un jugador en un partido específico.
    """
    queryset = Tarjeta.objects.all().select_related('jugador', 'partido')
    serializer_class = TarjetaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['jugador__primer_nombre', 'jugador__primer_apellido']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todas las tarjetas (con logging)"""
        logger.info(f"Listando tarjetas - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene una tarjeta específica (con logging)"""
        logger.info(f"Obteniendo detalle de la tarjeta {kwargs.get('pk')} - Usuario: {request.user}")
        return super().retrieve(request, *args, **kwargs)

    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """
        Filtrar tarjetas por tipo (AMARILLA o ROJA).
        
        Parámetros:
        - tipo: Tipo de tarjeta (AMARILLA o ROJA)
        
        Retorna:
        - Lista de tarjetas del tipo especificado
        """
        tipo = request.query_params.get('tipo', '').upper()
        logger.info(f"Buscando tarjetas de tipo: {tipo} - Usuario: {request.user}")
        
        if tipo not in ['AMARILLA', 'ROJA']:
            logger.warning(f"Tipo de tarjeta inválido: {tipo} - Usuario: {request.user}")
            return Response({"error": "El tipo debe ser 'AMARILLA' o 'ROJA'"}, status=400)
        
        queryset = Tarjeta.objects.filter(tipo=tipo).select_related('jugador', 'partido')
        serializer = self.get_serializer(queryset, many=True)
        
        logger.info(f"Tarjetas encontradas de tipo {tipo}: {queryset.count()}")
        return Response(serializer.data)
