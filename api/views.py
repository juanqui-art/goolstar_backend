from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from .models import Categoria, Equipo, Jugador, Jornada, Partido, Gol, Tarjeta
from .models.base import Torneo
from .models.estadisticas import EstadisticaEquipo
from .serializers import (
    CategoriaSerializer, EquipoSerializer, JugadorSerializer, JornadaSerializer,
    PartidoSerializer, GolSerializer, TarjetaSerializer,
    EquipoDetalleSerializer, PartidoDetalleSerializer,
    TorneoSerializer, TorneoDetalleSerializer, EstadisticaEquipoSerializer,
    TablaposicionesSerializer
)

from api.utils.logging_utils import get_logger, log_api_request
from api.utils.date_utils import get_today_date, date_to_datetime
from api.utils.tz_logging import log_timezone_operation, detect_naive_datetime, log_date_conversion

logger = get_logger(__name__)

class CategoriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las Categorías de los torneos.
    
    Una categoría representa una división dentro del torneo, como 'Sub-12', 'Senior', etc.
    """
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']
    permission_classes = [IsAuthenticatedOrReadOnly]

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

class JornadaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las Jornadas de los torneos.
    
    Una jornada agrupa varios partidos dentro de un torneo.
    """
    queryset = Jornada.objects.all().select_related('torneo').order_by('numero')
    serializer_class = JornadaSerializer
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

class PartidoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Partidos de los torneos.
    
    Un partido se juega entre dos equipos, pertenece a una jornada y tiene registros
    asociados como goles y tarjetas.
    """
    queryset = Partido.objects.all().select_related('equipo_1', 'equipo_2', 'jornada', 'torneo')
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
                partidos = Partido.objects.filter(jornada_id=jornada_id).order_by('fecha')
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
                partidos = partidos.order_by('fecha')
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
        from django.utils import timezone
        import datetime
        from api.utils.date_utils import get_today_date, date_to_datetime, get_date_range
        
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
            ).select_related('equipo_1', 'equipo_2', 'torneo', 'jornada').order_by('fecha')
            
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

class TorneoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Torneos.
    
    Un torneo es la competición principal que agrupa equipos, partidos y estadísticas.
    """
    queryset = Torneo.objects.all().select_related('categoria').order_by('-fecha_inicio')
    serializer_class = TorneoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'categoria__nombre']
    ordering_fields = ['nombre', 'fecha_inicio', 'categoria']
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TorneoDetalleSerializer
        return TorneoSerializer
    
    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Lista todos los torneos (con logging)"""
        logger.info(f"Listando torneos - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @log_api_request(logger)
    def retrieve(self, request, *args, **kwargs):
        """Obtiene un torneo específico (con logging)"""
        logger.info(f"Obteniendo detalle del torneo {kwargs.get('pk')} - Usuario: {request.user}")
        return super().retrieve(request, *args, **kwargs)

    @log_api_request(logger)
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        Obtener lista de torneos activos.
        
        Retorna:
        - Lista de torneos que están actualmente en curso, ordenados por fecha de inicio.
        """
        logger.info(f"Buscando torneos activos - Usuario: {request.user}")
        
        # Fecha actual (usando utilidad de zona horaria)
        today = get_today_date()
        logger.debug(f"Fecha actual para filtro de torneos activos: {today}")
        
        # Convertir date a datetime para el filtrado
        today_datetime = date_to_datetime(today)
        log_date_conversion(today, today_datetime, logger)
        
        queryset = Torneo.objects.filter(
            fecha_inicio__lte=today_datetime,
            fecha_fin__gte=today_datetime
        ).select_related('categoria').order_by('fecha_inicio')
        
        serializer = self.get_serializer(queryset, many=True)
        logger.info(f"Torneos activos encontrados: {queryset.count()}")
        
        return Response(serializer.data)
    
    @log_api_request(logger)
    @action(detail=True, methods=['get'])
    def tabla_posiciones(self, request, pk=None):
        """
        Obtener tabla de posiciones del torneo.
        
        Parámetros:
        - grupo: (opcional) Filtrar por grupo específico (A, B, C, etc.)
        
        Retorna:
        - Tabla de posiciones con estadísticas de equipos ordenadas por puntos,
          diferencia de goles y goles a favor.
        """
        torneo = self.get_object()
        grupo = request.query_params.get('grupo')
        
        # Base query para estadísticas
        estadisticas_query = EstadisticaEquipo.objects.filter(
            torneo=torneo
        ).select_related('equipo').order_by('-puntos', '-diferencia_goles', '-goles_favor')
        
        # Si se especifica un grupo, filtrar por grupo
        if grupo:
            estadisticas_query = estadisticas_query.filter(equipo__grupo=grupo.upper())
        
        serializer = EstadisticaEquipoSerializer(estadisticas_query, many=True)
        
        # Preparamos la respuesta con el formato adecuado
        response_data = {
            'grupo': grupo.upper() if grupo else 'Todos',
            'equipos': serializer.data
        }
        return Response(response_data)
    
    @log_api_request(logger)
    @action(detail=True, methods=['get'])
    def estadisticas(self, request, pk=None):
        """
        Obtener estadísticas generales del torneo.
        
        Retorna:
        - Estadísticas detalladas del torneo, incluyendo total de equipos, partidos,
          goles, tarjetas y más.
        """
        torneo = self.get_object()
        total_equipos = torneo.equipos.filter(activo=True).count()
        total_partidos = torneo.partidos.count()
        partidos_jugados = torneo.partidos.filter(completado=True).count()
        partidos_pendientes = total_partidos - partidos_jugados
        
        # Estadísticas de goles
        total_goles = Gol.objects.filter(partido__torneo=torneo).count()
        promedio_goles = total_goles / partidos_jugados if partidos_jugados > 0 else 0
        
        # Estadísticas de tarjetas
        tarjetas_amarillas = Tarjeta.objects.filter(partido__torneo=torneo, tipo='AMARILLA').count()
        tarjetas_rojas = Tarjeta.objects.filter(partido__torneo=torneo, tipo='ROJA').count()
        
        # Equipo más goleador y menos goleado
        estadisticas = EstadisticaEquipo.objects.filter(torneo=torneo).select_related('equipo')
        equipo_mas_goleador = estadisticas.order_by('-goles_favor').first()
        equipo_menos_goleado = estadisticas.filter(partidos_jugados__gt=0).order_by('goles_contra').first()
        
        response_data = {
            'torneo': TorneoSerializer(torneo).data,
            'estadisticas_generales': {
                'total_equipos': total_equipos,
                'total_partidos': total_partidos,
                'partidos_jugados': partidos_jugados,
                'partidos_pendientes': partidos_pendientes,
                'total_goles': total_goles,
                'promedio_goles_por_partido': round(promedio_goles, 2),
                'tarjetas_amarillas': tarjetas_amarillas,
                'tarjetas_rojas': tarjetas_rojas,
            },
            'mejores_equipos': {
                'equipo_mas_goleador': {
                    'nombre': equipo_mas_goleador.equipo.nombre if equipo_mas_goleador else None,
                    'goles': equipo_mas_goleador.goles_favor if equipo_mas_goleador else 0
                },
                'equipo_menos_goleado': {
                    'nombre': equipo_menos_goleado.equipo.nombre if equipo_menos_goleado else None,
                    'goles_en_contra': equipo_menos_goleado.goles_contra if equipo_menos_goleado else 0
                }
            }
        }
        
        return Response(response_data)
        
    @log_api_request(logger)
    @action(detail=True, methods=['get'])
    def jugadores_destacados(self, request, pk=None):
        """
        Obtener jugadores destacados del torneo.
        
        Parámetros:
        - limite: (opcional) Número máximo de jugadores a mostrar en cada categoría (por defecto: 5)
        
        Retorna:
        - Lista de goleadores, jugadores con tarjetas amarillas y jugadores con tarjetas rojas
        """
        from django.db.models import Count, Sum, F, Q
        
        torneo = self.get_object()
        limite = request.query_params.get('limite', 5)
        
        try:
            limite = int(limite)
        except (ValueError, TypeError):
            limite = 5
        
        # 1. Obtener goleadores (jugadores con más goles)
        goleadores = (
            Jugador.objects.filter(goles__partido__torneo=torneo)
            .annotate(total_goles=Count('goles'))
            .select_related('equipo')
            .order_by('-total_goles')[:limite]
        )
        
        # 2. Obtener jugadores con más tarjetas amarillas
        tarjetas_amarillas = (
            Jugador.objects.filter(tarjetas__partido__torneo=torneo, tarjetas__tipo='AMARILLA')
            .annotate(total_amarillas=Count('tarjetas', filter=Q(tarjetas__tipo='AMARILLA')))
            .select_related('equipo')
            .order_by('-total_amarillas')[:limite]
        )
        
        # 3. Obtener jugadores con tarjetas rojas
        tarjetas_rojas = (
            Jugador.objects.filter(tarjetas__partido__torneo=torneo, tarjetas__tipo='ROJA')
            .annotate(total_rojas=Count('tarjetas', filter=Q(tarjetas__tipo='ROJA')))
            .select_related('equipo')
            .order_by('-total_rojas')[:limite]
        )
        
        # Formatear respuesta
        response_data = {
            'torneo': TorneoSerializer(torneo).data,
            'goleadores': [
                {
                    'jugador': f"{j.primer_nombre} {j.primer_apellido}",
                    'cedula': j.cedula,
                    'equipo': j.equipo.nombre,
                    'goles': j.total_goles
                } for j in goleadores
            ],
            'tarjetas_amarillas': [
                {
                    'jugador': f"{j.primer_nombre} {j.primer_apellido}",
                    'cedula': j.cedula,
                    'equipo': j.equipo.nombre,
                    'amarillas': j.total_amarillas
                } for j in tarjetas_amarillas
            ],
            'tarjetas_rojas': [
                {
                    'jugador': f"{j.primer_nombre} {j.primer_apellido}",
                    'cedula': j.cedula,
                    'equipo': j.equipo.nombre,
                    'rojas': j.total_rojas
                } for j in tarjetas_rojas
            ]
        }
        
        return Response(response_data)
