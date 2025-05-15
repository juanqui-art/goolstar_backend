"""
Vistas relacionadas con la gestión de Categorías en el sistema.
"""
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from api.models import Categoria
from api.serializers import CategoriaSerializer
from api.utils.logging_utils import get_logger

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
