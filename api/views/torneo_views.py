"""
Vistas relacionadas con la gestión de Torneos en el sistema.
"""
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend  # ← LÍNEA 1 NUEVA
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from api.models import Torneo, Gol, Tarjeta, Jugador
from api.models.estadisticas import EstadisticaEquipo
from api.serializers import (
    TorneoSerializer, TorneoDetalleSerializer,
    EstadisticaEquipoSerializer, TablaposicionesSerializer
)
from api.utils.date_utils import get_today_date, date_to_datetime
from api.utils.logging_utils import get_logger, log_api_request
from api.utils.tz_logging import log_date_conversion

logger = get_logger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="Listar todos los torneos",
        description="Retorna una lista paginada de todos los torneos en el sistema."
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de un torneo",
        description="Retorna información detallada de un torneo específico."
    ),
    create=extend_schema(
        summary="Crear un nuevo torneo",
        description="Crea un nuevo torneo con los datos proporcionados."
    ),
    update=extend_schema(
        summary="Actualizar un torneo completo",
        description="Actualiza todos los campos de un torneo existente."
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente un torneo",
        description="Actualiza solo los campos proporcionados de un torneo existente."
    ),
    destroy=extend_schema(
        summary="Eliminar un torneo",
        description="Elimina un torneo existente del sistema."
    )
)
class TorneoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Torneos.

    Un torneo es la competición principal que agrupa equipos, partidos y estadísticas.
    """
    queryset = Torneo.objects.all().select_related('categoria').order_by('-fecha_inicio')
    serializer_class = TorneoSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,
                       filters.OrderingFilter]  # ← MODIFICAR: agregar DjangoFilterBackend
    filterset_fields = ['activo', 'finalizado', 'fase_actual', 'categoria']  # ← LÍNEA 2 NUEVA
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

    @extend_schema(
        summary="Listar torneos activos",
        description="Obtiene una lista de torneos que están actualmente en curso (fecha actual entre fecha_inicio y fecha_fin).",
        responses={200: TorneoSerializer(many=True)}
    )
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

        # Crear query base con torneos marcados como activos
        queryset = Torneo.objects.filter(
            activo=True,  # Considerar el campo activo del modelo
            fecha_inicio__lte=today_datetime
        ).select_related('categoria')

        # Añadir condición para fecha_fin solo si queremos filtrar por ella
        # Esto permite que torneos con fecha_fin=None también aparezcan
        fecha_fin_filter = Q(fecha_fin__gte=today_datetime) | Q(fecha_fin__isnull=True)
        queryset = queryset.filter(fecha_fin_filter).order_by('fecha_inicio')

        logger.info(f"Torneos activos encontrados: {queryset.count()}")
        serializer = self.get_serializer(queryset, many=True)

        return Response(serializer.data)

    @extend_schema(
        summary="Obtener tabla de posiciones",
        description="Obtiene la tabla de posiciones actual del torneo, con estadísticas de cada equipo.",
        parameters=[
            OpenApiParameter(
                name="grupo",
                description="Filtrar por grupo específico (A, B, C, etc.)",
                required=False,
                type=str
            ),
            OpenApiParameter(
                name="actualizar",
                description="Si es 'true', fuerza la actualización de todas las estadísticas",
                required=False,
                type=bool,
                default=False
            ),
        ],
        responses={200: TablaposicionesSerializer}
    )
    @log_api_request(logger)
    @action(detail=True, methods=['get'])
    def tabla_posiciones(self, request, pk=None):
        """Obtener tabla de posiciones del torneo."""
        torneo = self.get_object()
        grupo = request.query_params.get('grupo')
        actualizar = request.query_params.get('actualizar', 'false').lower() == 'true'

        # Base query para estadísticas
        estadisticas_query = EstadisticaEquipo.objects.filter(
            torneo=torneo
        ).select_related('equipo').order_by('-puntos', '-diferencia_goles', '-goles_favor')

        # Si se especifica un grupo específico
        if grupo:
            estadisticas_query = estadisticas_query.filter(equipo__grupo=grupo.upper())
            serializer = EstadisticaEquipoSerializer(estadisticas_query, many=True)

            response_data = {
                'grupo': grupo.upper(),
                'equipos': serializer.data
            }
        else:
            # ✅ NUEVA LÓGICA: Agrupar automáticamente
            from collections import defaultdict

            grupos_data = defaultdict(list)

            # Obtener todas las estadísticas
            all_estadisticas = estadisticas_query
            serializer = EstadisticaEquipoSerializer(all_estadisticas, many=True)

            # Agrupar por grupo
            for equipo_data in serializer.data:
                grupo_letra = equipo_data.get('grupo')
                if grupo_letra:
                    grupos_data[grupo_letra].append(equipo_data)

            # Ordenar cada grupo internamente
            for grupo_letra in grupos_data:
                grupos_data[grupo_letra] = sorted(
                    grupos_data[grupo_letra],
                    key=lambda x: (-x['puntos'], -x['diferencia_goles'], -x['goles_favor'])
                )

            response_data = {
                'grupos': dict(grupos_data),
                'torneo_id': torneo.id,
                'tiene_fase_grupos': torneo.tiene_fase_grupos,
                'total_equipos': len(all_estadisticas)
            }

        return Response(response_data)

    @extend_schema(
        summary="Obtener estadísticas generales del torneo",
        description="Obtiene estadísticas detalladas del torneo, incluyendo total de equipos, partidos, goles, tarjetas y más.",
        responses={200: None}
    )
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

    @extend_schema(
        summary="Obtener jugadores destacados del torneo",
        description="Obtiene lista de goleadores, jugadores con tarjetas amarillas y jugadores con tarjetas rojas.",
        parameters=[
            OpenApiParameter(
                name="limite",
                description="Número máximo de jugadores a mostrar en cada categoría (por defecto: 5)",
                required=False,
                type=int,
                default=5
            ),
        ],
        responses={200: None}
    )
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
