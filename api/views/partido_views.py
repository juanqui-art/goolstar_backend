"""
Vistas relacionadas con la gestión de Partidos en el sistema.
"""
from django.db.models import Q
import datetime

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Partido
from api.serializers import PartidoSerializer, PartidoDetalleSerializer
from api.utils.logging_utils import get_logger, log_api_request
from api.utils.date_utils import get_today_date, get_date_range

logger = get_logger(__name__)

class PartidoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Partidos de los torneos.
    
    Un partido se juega entre dos equipos, pertenece a una jornada y tiene registros
    asociados como goles y tarjetas.
    """
    queryset = Partido.objects.all().select_related('equipo_1', 'equipo_2', 'jornada', 'torneo').prefetch_related(
        'goles__jugador__equipo',  # Optimizar goles con jugador y equipo
        'tarjetas__jugador__equipo'  # Optimizar tarjetas con jugador y equipo
    ).order_by('-fecha', 'id')
    serializer_class = PartidoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['fecha']
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PartidoDetalleSerializer
        return PartidoSerializer
    
    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todos los partidos (con logging)"""
        logger.info(f"Listando partidos - Filtros: {request.query_params}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un partido específico (con logging)"""
        partido_id = kwargs.get('pk')
        logger.info(f"Obteniendo detalles del partido: {partido_id}")
        return super().retrieve(request, *args, **kwargs)
    
    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def por_jornada(self, request):
        """
        Filtrar partidos por jornada.
        
        Parámetros:
        - jornada_id: ID de la jornada para filtrar los partidos
        
        Retorna:
        - Lista de partidos de la jornada especificada ordenados por fecha
        """
        jornada_id = request.query_params.get('jornada_id')
        logger.info(
            f"Filtrando partidos por jornada: {jornada_id}"
        )
        
        if jornada_id:
            try:
                partidos = Partido.objects.filter(jornada_id=jornada_id).select_related('equipo_1', 'equipo_2', 'jornada', 'torneo').prefetch_related('goles', 'tarjetas').order_by('fecha')
                serializer = self.get_serializer(partidos, many=True)
                logger.info(f"Encontrados {len(partidos)} partidos para la jornada {jornada_id}")
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Error al filtrar partidos por jornada {jornada_id}: {str(e)}")
                return Response({"error": f"Error al procesar la solicitud: {str(e)}"}, status=500)
                
        logger.warning("Solicitud de filtrado por jornada sin jornada_id")
        return Response({"error": "Se requiere el parámetro jornada_id"}, status=400)
    
    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def por_equipo(self, request):
        """
        Filtrar partidos por equipo.
        
        Parámetros:
        - equipo_id: ID del equipo para filtrar los partidos
        
        Retorna:
        - Lista de partidos donde el equipo ha participado, ordenados por fecha
        """
        equipo_id = request.query_params.get('equipo_id')
        logger.info(f"Filtrando partidos por equipo: {equipo_id}")
        
        if equipo_id:
            try:
                partidos = Partido.objects.filter(equipo_1_id=equipo_id) | Partido.objects.filter(equipo_2_id=equipo_id)
                partidos = partidos.select_related('equipo_1', 'equipo_2', 'jornada', 'torneo').prefetch_related('goles', 'tarjetas').order_by('fecha')
                serializer = self.get_serializer(partidos, many=True)
                logger.info(f"Encontrados {len(partidos)} partidos para el equipo {equipo_id}")
                return Response(serializer.data)
            except Exception as e:
                logger.error(f"Error al filtrar partidos por equipo {equipo_id}: {str(e)}")
                return Response({"error": f"Error al procesar la solicitud: {str(e)}"}, status=500)
                
        logger.warning("Solicitud de filtrado por equipo sin equipo_id")
        return Response({"error": "Se requiere el parámetro equipo_id"}, status=400)
    
    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """
        Obtener partidos próximos a disputarse.
        
        Parámetros de filtrado:
        - torneo_id: (opcional) Filtra partidos por torneo
        - equipo_id: (opcional) Filtra partidos donde participa un equipo específico
        - dias: (opcional) Número de días hacia adelante para limitar la búsqueda (default: 7)
        
        Retorna:
        - Lista de partidos próximos ordenados por fecha
        """
        # Parámetros de filtrado
        torneo_id = request.query_params.get('torneo_id')
        equipo_id = request.query_params.get('equipo_id')
        dias = request.query_params.get('dias', 7)
        
        logger.info(
            f"Buscando próximos partidos - Filtros: torneo={torneo_id}, "
            f"equipo={equipo_id}, días={dias}"
        )
        
        try:
            dias = int(dias)
        except (ValueError, TypeError):
            logger.warning(f"Valor de días inválido: '{dias}'. Usando valor por defecto: 7")
            dias = 7
        
        try:
            # Obtener fechas con manejo adecuado de zona horaria
            fecha_actual = get_today_date()
            fecha_limite = fecha_actual + datetime.timedelta(days=dias)
            
            logger.debug(
                f"Rango de fechas: desde {fecha_actual.isoformat()} "
                f"hasta {fecha_limite.isoformat()}"
            )
            
            # Convertir a datetime con zona horaria para el filtrado
            fecha_inicio_dt, fecha_fin_dt = get_date_range(fecha_actual, dias)
            
            # Construimos el query base
            queryset = Partido.objects.filter(
                fecha__gte=fecha_inicio_dt,
                fecha__lte=fecha_fin_dt,
                completado=False
            ).select_related('equipo_1', 'equipo_2', 'torneo', 'jornada').prefetch_related('goles', 'tarjetas').order_by('fecha')
            
            # Aplicamos filtros adicionales si existen
            if torneo_id:
                queryset = queryset.filter(torneo_id=torneo_id)
                
            if equipo_id:
                queryset = queryset.filter(
                    Q(equipo_1_id=equipo_id) | Q(equipo_2_id=equipo_id)
                )
            
            serializer = PartidoDetalleSerializer(queryset, many=True)
            
            logger.info(f"Encontrados {queryset.count()} partidos próximos")
            
            return Response({
                'periodo': {
                    'desde': fecha_actual.strftime('%Y-%m-%d'),
                    'hasta': fecha_limite.strftime('%Y-%m-%d'),
                },
                'total_partidos': queryset.count(),
                'partidos': serializer.data
            })
            
        except Exception as e:
            logger.error(f"Error al buscar partidos próximos: {str(e)}", exc_info=True)
            return Response(
                {"error": "Se produjo un error al procesar la solicitud"}, 
                status=500
            )
