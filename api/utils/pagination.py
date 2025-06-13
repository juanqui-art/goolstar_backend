"""
Utilidades de paginación optimizadas para el sistema GoolStar.
"""

from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict


class OptimizedCursorPagination(CursorPagination):
    """
    Paginación cursor optimizada para mejor rendimiento en listas grandes.
    Usa cursor pagination que es más eficiente que offset/limit.
    """
    page_size = 20
    max_page_size = 100
    ordering = '-id'  # Por defecto ordenar por ID descendente
    cursor_query_param = 'cursor'
    page_size_query_param = 'page_size'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('count', None),  # Cursor pagination no calcula count por performance
            ('results', data)
        ]))


class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Paginación por número de página optimizada.
    Úsala solo cuando necesites mostrar número total de páginas.
    """
    page_size = 20
    max_page_size = 100
    page_size_query_param = 'page_size'
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class TorneoPagination(OptimizedCursorPagination):
    """Paginación específica para torneos (ordenado por fecha)"""
    page_size = 10
    ordering = '-fecha_inicio'


class EquipoPagination(OptimizedCursorPagination):
    """Paginación específica para equipos (ordenado por nombre)"""
    page_size = 25
    ordering = 'nombre'


class PartidoPagination(OptimizedCursorPagination):
    """Paginación específica para partidos (ordenado por fecha)"""
    page_size = 15
    ordering = '-fecha'


class JugadorPagination(OptimizedCursorPagination):
    """Paginación específica para jugadores (ordenado por apellido)"""
    page_size = 30
    ordering = 'primer_apellido'


class GolTarjetaPagination(OptimizedCursorPagination):
    """Paginación específica para goles y tarjetas (ordenado por fecha)"""
    page_size = 50
    ordering = '-fecha'