from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
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

class EquipoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Equipos participantes en los torneos.
    
    Un equipo pertenece a una categoría y tiene múltiples jugadores.
    """
    queryset = Equipo.objects.all()
    serializer_class = EquipoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre', 'categoria']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EquipoDetalleSerializer
        return EquipoSerializer
    
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
        if categoria_id:
            equipos = Equipo.objects.filter(categoria_id=categoria_id)
            serializer = self.get_serializer(equipos, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro categoria_id"}, status=400)

class JugadorViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Jugadores de los equipos.
    
    Un jugador pertenece a un equipo y puede tener estadísticas como goles y tarjetas.
    """
    queryset = Jugador.objects.all()
    serializer_class = JugadorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['primer_nombre', 'primer_apellido', 'cedula']
    ordering_fields = ['primer_apellido', 'primer_nombre']
    
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
        if equipo_id:
            jugadores = Jugador.objects.filter(equipo_id=equipo_id)
            serializer = self.get_serializer(jugadores, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro equipo_id"}, status=400)
    
    @action(detail=False, methods=['get'])
    def goleadores(self, request):
        """
        Obtener lista de jugadores con sus estadísticas de goles.
        
        Retorna:
        - Lista de jugadores ordenados por la cantidad de goles marcados (descendente)
        """
        jugadores = Jugador.objects.annotate(total_goles=Count('goles')).filter(total_goles__gt=0).order_by('-total_goles')
        serializer = JugadorSerializer(jugadores, many=True)
        data = serializer.data
        for i, jugador in enumerate(data):
            jugador['total_goles'] = jugadores[i].total_goles
        return Response(data)

class JornadaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las Jornadas de los torneos.
    
    Una jornada representa una fecha o ronda del torneo y contiene múltiples partidos.
    """
    queryset = Jornada.objects.all().order_by('numero')
    serializer_class = JornadaSerializer

class PartidoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Partidos de los torneos.
    
    Un partido se juega entre dos equipos, pertenece a una jornada y tiene registros
    asociados como goles y tarjetas.
    """
    queryset = Partido.objects.all()
    serializer_class = PartidoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    ordering_fields = ['fecha']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PartidoDetalleSerializer
        return PartidoSerializer
    
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
        if jornada_id:
            partidos = Partido.objects.filter(jornada_id=jornada_id).order_by('fecha')
            serializer = self.get_serializer(partidos, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro jornada_id"}, status=400)
    
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
        if equipo_id:
            partidos = Partido.objects.filter(equipo_1_id=equipo_id) | Partido.objects.filter(equipo_2_id=equipo_id)
            partidos = partidos.order_by('fecha')
            serializer = self.get_serializer(partidos, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro equipo_id"}, status=400)
    
    @action(detail=False, methods=['get'])
    def proximos(self, request):
        """
        Obtener próximos partidos programados.
        
        Parámetros:
        - torneo_id: (opcional) ID del torneo para filtrar los partidos
        - dias: (opcional) Número de días hacia adelante para buscar (por defecto: 7)
        - equipo_id: (opcional) ID del equipo para filtrar partidos específicos
        
        Retorna:
        - Lista de partidos próximos ordenados por fecha
        """
        from django.utils import timezone
        import datetime
        
        # Parámetros de filtrado
        torneo_id = request.query_params.get('torneo_id')
        equipo_id = request.query_params.get('equipo_id')
        dias = request.query_params.get('dias', 7)
        
        try:
            dias = int(dias)
        except (ValueError, TypeError):
            dias = 7
            
        # Fecha actual y fecha límite
        fecha_actual = timezone.now().date()
        fecha_limite = fecha_actual + datetime.timedelta(days=dias)
        
        # Construimos el query base
        queryset = Partido.objects.filter(
            fecha__gte=fecha_actual,
            fecha__lte=fecha_limite,
            completado=False
        ).select_related('equipo_1', 'equipo_2', 'jornada').order_by('fecha')
        
        # Aplicamos filtros adicionales si existen
        if torneo_id:
            queryset = queryset.filter(torneo_id=torneo_id)
            
        if equipo_id:
            queryset = queryset.filter(
                Q(equipo_1_id=equipo_id) | Q(equipo_2_id=equipo_id)
            )
        
        serializer = PartidoDetalleSerializer(queryset, many=True)
        
        return Response({
            'periodo': {
                'desde': fecha_actual.strftime('%Y-%m-%d'),
                'hasta': fecha_limite.strftime('%Y-%m-%d'),
            },
            'total_partidos': queryset.count(),
            'partidos': serializer.data
        })

class GolViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Goles marcados en los partidos.
    
    Un gol es anotado por un jugador en un partido específico.
    """
    queryset = Gol.objects.all()
    serializer_class = GolSerializer
    
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
        if partido_id:
            goles = Gol.objects.filter(partido_id=partido_id)
            serializer = self.get_serializer(goles, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro partido_id"}, status=400)

class TarjetaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar las Tarjetas (amarillas y rojas) mostradas en los partidos.
    
    Una tarjeta es mostrada a un jugador en un partido específico.
    """
    queryset = Tarjeta.objects.all()
    serializer_class = TarjetaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['jugador__primer_nombre', 'jugador__primer_apellido']
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """
        Filtrar tarjetas por tipo (AMARILLA o ROJA).
        
        Parámetros:
        - tipo: Tipo de tarjeta (AMARILLA o ROJA)
        
        Retorna:
        - Lista de tarjetas del tipo especificado
        """
        tipo = request.query_params.get('tipo')
        if tipo:
            tarjetas = Tarjeta.objects.filter(tipo=tipo.upper())
            serializer = self.get_serializer(tarjetas, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro tipo (AMARILLA o ROJA)"}, status=400)

class TorneoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar los Torneos.
    
    Un torneo es la competición principal que agrupa equipos, partidos y estadísticas.
    """
    queryset = Torneo.objects.all().order_by('-fecha_inicio')
    serializer_class = TorneoSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'categoria__nombre']
    ordering_fields = ['nombre', 'fecha_inicio', 'categoria']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TorneoDetalleSerializer
        return TorneoSerializer
    
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        Obtener lista de torneos activos.
        
        Retorna:
        - Lista de torneos que están actualmente en curso, ordenados por fecha de inicio.
        """
        torneos_activos = Torneo.objects.filter(activo=True, finalizado=False).order_by('-fecha_inicio')
        serializer = self.get_serializer(torneos_activos, many=True)
        return Response(serializer.data)
    
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
