"""
Vistas relacionadas con la gestión de Equipos en el sistema.
"""
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Equipo
from api.serializers import EquipoSerializer, EquipoDetalleSerializer
from api.utils.logging_utils import get_logger, log_api_request

logger = get_logger(__name__)

class EquipoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Equipos participantes en los torneos.
    
    Un equipo pertenece a una categoría y tiene múltiples jugadores.
    """
    queryset = Equipo.objects.all().select_related('categoria', 'torneo')
    serializer_class = EquipoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'categoria']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EquipoDetalleSerializer
        return EquipoSerializer
    
    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todos los equipos (con logging)"""
        logger.info(f"Listando equipos - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un equipo específico (con logging)"""
        logger.info(f"Obteniendo detalle del equipo {kwargs.get('pk')} - Usuario: {request.user}")
        return super().retrieve(request, *args, **kwargs)
    
    @log_api_request(logger)
    def create(self, request, *args, **kwargs):
        """Crea un nuevo equipo (con logging)"""
        logger.info(f"Creando nuevo equipo - Usuario: {request.user}")
        return super().create(request, *args, **kwargs)
    
    @log_api_request(logger)
    def update(self, request, *args, **kwargs):
        """Actualiza un equipo (con logging)"""
        logger.info(f"Actualizando equipo {kwargs.get('pk')} - Usuario: {request.user}")
        return super().update(request, *args, **kwargs)
    
    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def por_categoria(self, request):
        """
        Filtrar equipos por categoría.
        
        Parámetros:
        - categoria_id: ID de la categoría para filtrar los equipos
        
        Retorna:
        - Lista de equipos que pertenecen a la categoría especificada
        """
        categoria_id = request.query_params.get('categoria_id')
        logger.info(f"Buscando equipos para la categoría ID: {categoria_id} - Usuario: {request.user}")
        
        if not categoria_id:
            logger.warning(f"Solicitud de equipos sin especificar categoria_id - Usuario: {request.user}")
            return Response({"error": "Debe especificar el parámetro categoria_id"}, status=400)
        
        equipos = Equipo.objects.filter(categoria_id=categoria_id)
        serializer = self.get_serializer(equipos, many=True)
        
        logger.info(f"Equipos encontrados para categoría ID {categoria_id}: {equipos.count()}")
        return Response(serializer.data)
