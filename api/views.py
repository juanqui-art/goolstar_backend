from rest_framework import viewsets, filters
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import Categoria, Equipo, Jugador, Jornada, Partido, Gol, Tarjeta
from .serializers import (
    CategoriaSerializer, EquipoSerializer, JugadorSerializer, JornadaSerializer,
    PartidoSerializer, GolSerializer, TarjetaSerializer,
    EquipoDetalleSerializer, PartidoDetalleSerializer
)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre']
    ordering_fields = ['nombre']

class EquipoViewSet(viewsets.ModelViewSet):
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
        categoria_id = request.query_params.get('categoria_id')
        if categoria_id:
            equipos = Equipo.objects.filter(categoria_id=categoria_id)
            serializer = self.get_serializer(equipos, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro categoria_id"}, status=400)

class JugadorViewSet(viewsets.ModelViewSet):
    queryset = Jugador.objects.all()
    serializer_class = JugadorSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['primer_nombre', 'primer_apellido', 'cedula']
    ordering_fields = ['primer_apellido', 'primer_nombre']
    
    @action(detail=False, methods=['get'])
    def por_equipo(self, request):
        equipo_id = request.query_params.get('equipo_id')
        if equipo_id:
            jugadores = Jugador.objects.filter(equipo_id=equipo_id)
            serializer = self.get_serializer(jugadores, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro equipo_id"}, status=400)
    
    @action(detail=False, methods=['get'])
    def goleadores(self, request):
        jugadores = Jugador.objects.annotate(total_goles=Count('goles')).filter(total_goles__gt=0).order_by('-total_goles')
        serializer = JugadorSerializer(jugadores, many=True)
        data = serializer.data
        for i, jugador in enumerate(data):
            jugador['total_goles'] = jugadores[i].total_goles
        return Response(data)

class JornadaViewSet(viewsets.ModelViewSet):
    queryset = Jornada.objects.all().order_by('numero')
    serializer_class = JornadaSerializer

class PartidoViewSet(viewsets.ModelViewSet):
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
        jornada_id = request.query_params.get('jornada_id')
        if jornada_id:
            partidos = Partido.objects.filter(jornada_id=jornada_id).order_by('fecha')
            serializer = self.get_serializer(partidos, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro jornada_id"}, status=400)
    
    @action(detail=False, methods=['get'])
    def por_equipo(self, request):
        equipo_id = request.query_params.get('equipo_id')
        if equipo_id:
            partidos = Partido.objects.filter(equipo_1_id=equipo_id) | Partido.objects.filter(equipo_2_id=equipo_id)
            partidos = partidos.order_by('fecha')
            serializer = self.get_serializer(partidos, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro equipo_id"}, status=400)

class GolViewSet(viewsets.ModelViewSet):
    queryset = Gol.objects.all()
    serializer_class = GolSerializer
    
    @action(detail=False, methods=['get'])
    def por_partido(self, request):
        partido_id = request.query_params.get('partido_id')
        if partido_id:
            goles = Gol.objects.filter(partido_id=partido_id)
            serializer = self.get_serializer(goles, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro partido_id"}, status=400)

class TarjetaViewSet(viewsets.ModelViewSet):
    queryset = Tarjeta.objects.all()
    serializer_class = TarjetaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['jugador__primer_nombre', 'jugador__primer_apellido']
    
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        tipo = request.query_params.get('tipo')
        if tipo:
            tarjetas = Tarjeta.objects.filter(tipo=tipo.upper())
            serializer = self.get_serializer(tarjetas, many=True)
            return Response(serializer.data)
        return Response({"error": "Se requiere el parámetro tipo (AMARILLA o ROJA)"}, status=400)
