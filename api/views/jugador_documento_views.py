"""
Vistas relacionadas con la gestión de Documentos de Jugadores.
Implementa endpoints seguros para subida, verificación y gestión de documentos de identidad.
"""

from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend

from api.models import JugadorDocumento, Jugador
from api.serializers import (
    JugadorDocumentoSerializer,
    JugadorDocumentoListSerializer,
    JugadorDocumentoUploadSerializer,
    JugadorDocumentoVerificationSerializer,
    JugadorConDocumentosSerializer
)
from api.utils.logging_utils import get_logger, log_api_request
from rest_framework.pagination import PageNumberPagination

logger = get_logger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    """Paginación estándar para documentos de jugadores."""
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 1000


class JugadorDocumentoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para gestionar documentos de jugadores.
    
    Proporciona funcionalidades completas para:
    - Subir documentos de identidad (DNI, cédula)
    - Verificar documentos
    - Listar y filtrar documentos
    - Gestionar estados de verificación
    """
    
    queryset = JugadorDocumento.objects.all().select_related(
        'jugador', 'verificado_por'
    )
    
    serializer_class = JugadorDocumentoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]  # Para subida de archivos
    filter_backends = [DjangoFilterBackend]
    ordering = ['-fecha_subida']  # Orden por defecto: documentos más recientes primero
    filterset_fields = {
        'jugador': ['exact'],
        'tipo_documento': ['exact', 'in'],
        'estado_verificacion': ['exact', 'in'],
        'fecha_subida': ['gte', 'lte'],
        'verificado_por': ['exact'],
    }
    
    def get_serializer_class(self):
        """Seleccionar serializer según la acción."""
        if self.action == 'list':
            return JugadorDocumentoListSerializer
        elif self.action == 'upload':
            return JugadorDocumentoUploadSerializer
        elif self.action in ['verify', 'reject']:
            return JugadorDocumentoVerificationSerializer
        return JugadorDocumentoSerializer
    
    def get_permissions(self):
        """
        Permisos diferenciados por acción.
        - Lectura: usuarios autenticados o solo lectura
        - Subida: usuarios autenticados
        - Verificación: solo staff
        """
        if self.action in ['verify', 'reject', 'destroy']:
            # Solo staff puede verificar, rechazar o eliminar
            permission_classes = [permissions.IsAdminUser]
        elif self.action in ['create', 'upload', 'update', 'partial_update']:
            # Solo usuarios autenticados pueden subir/modificar
            permission_classes = [permissions.IsAuthenticated]
        else:
            # Lectura para usuarios autenticados o solo lectura
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    @log_api_request(logger)
    def create(self, request, *args, **kwargs):
        """Crear un nuevo documento de jugador."""
        logger.info(f"Subiendo documento - Usuario: {request.user}")
        return super().create(request, *args, **kwargs)
    
    @log_api_request(logger)
    def list(self, request, *args, **kwargs):
        """Listar documentos con filtros."""
        logger.info(f"Listando documentos - Usuario: {request.user}")
        return super().list(request, *args, **kwargs)
    
    @action(detail=False, methods=['post'], url_path='upload')
    @log_api_request(logger)
    def upload(self, request):
        """
        Endpoint específico para subida de documentos.
        
        POST /api/jugador-documentos/upload/
        """
        logger.info(f"Upload de documento - Usuario: {request.user}")
        
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Verificar que el jugador existe
            jugador_id = serializer.validated_data.get('jugador')
            if not Jugador.objects.filter(id=jugador_id.id).exists():
                return Response(
                    {'error': 'Jugador no encontrado'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            documento = serializer.save()
            logger.info(
                f"Documento subido exitosamente - ID: {documento.id}, "
                f"Jugador: {documento.jugador}, Tipo: {documento.tipo_documento}"
            )
            
            # Retornar con serializer completo para mostrar todos los datos
            response_serializer = JugadorDocumentoSerializer(documento)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning(f"Error en upload de documento: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['patch'], url_path='verify')
    @log_api_request(logger)
    def verify(self, request, pk=None):
        """
        Verificar un documento como válido.
        
        PATCH /api/jugador-documentos/{id}/verify/
        """
        documento = self.get_object()
        logger.info(f"Verificando documento {documento.id} - Usuario: {request.user}")
        
        comentarios = request.data.get('comentarios_verificacion', '')
        
        try:
            documento.marcar_como_verificado(request.user, comentarios)
            logger.info(f"Documento {documento.id} verificado exitosamente")
            
            serializer = JugadorDocumentoSerializer(documento)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error al verificar documento {documento.id}: {str(e)}")
            return Response(
                {'error': f'Error al verificar documento: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['patch'], url_path='reject')
    @log_api_request(logger)
    def reject(self, request, pk=None):
        """
        Rechazar un documento con comentarios obligatorios.
        
        PATCH /api/jugador-documentos/{id}/reject/
        """
        documento = self.get_object()
        logger.info(f"Rechazando documento {documento.id} - Usuario: {request.user}")
        
        serializer = self.get_serializer(documento, data=request.data, partial=True)
        if serializer.is_valid():
            comentarios = serializer.validated_data.get('comentarios_verificacion')
            
            if not comentarios:
                return Response(
                    {'error': 'Los comentarios son obligatorios para rechazar un documento'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                documento.rechazar_documento(request.user, comentarios)
                logger.info(f"Documento {documento.id} rechazado exitosamente")
                
                response_serializer = JugadorDocumentoSerializer(documento)
                return Response(response_serializer.data)
                
            except Exception as e:
                logger.error(f"Error al rechazar documento {documento.id}: {str(e)}")
                return Response(
                    {'error': f'Error al rechazar documento: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        logger.warning(f"Error en rechazo de documento: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='by-jugador/(?P<jugador_id>[^/.]+)')
    @log_api_request(logger)
    def by_jugador(self, request, jugador_id=None):
        """
        Obtener todos los documentos de un jugador específico.
        
        GET /api/jugador-documentos/by-jugador/{jugador_id}/
        """
        logger.info(f"Consultando documentos del jugador {jugador_id} - Usuario: {request.user}")
        
        try:
            jugador = Jugador.objects.get(id=jugador_id)
        except Jugador.DoesNotExist:
            return Response(
                {'error': 'Jugador no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        documentos = self.queryset.filter(jugador=jugador)
        
        page = self.paginate_queryset(documentos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(documentos, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='pending')
    @log_api_request(logger)
    def pending(self, request):
        """
        Obtener documentos pendientes de verificación.
        
        GET /api/jugador-documentos/pending/
        """
        logger.info(f"Consultando documentos pendientes - Usuario: {request.user}")
        
        documentos_pendientes = self.queryset.filter(
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        )
        
        page = self.paginate_queryset(documentos_pendientes)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(documentos_pendientes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='stats')
    @log_api_request(logger)
    def stats(self, request):
        """
        Obtener estadísticas de documentos.
        
        GET /api/jugador-documentos/stats/
        """
        logger.info(f"Consultando estadísticas de documentos - Usuario: {request.user}")
        
        total_documentos = self.queryset.count()
        documentos_verificados = self.queryset.filter(
            estado_verificacion=JugadorDocumento.EstadoVerificacion.VERIFICADO
        ).count()
        documentos_pendientes = self.queryset.filter(
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        ).count()
        documentos_rechazados = self.queryset.filter(
            estado_verificacion=JugadorDocumento.EstadoVerificacion.RECHAZADO
        ).count()
        
        # Estadísticas por tipo de documento
        tipos_stats = {}
        for tipo_choice in JugadorDocumento.TipoDocumento.choices:
            tipo_code, tipo_name = tipo_choice
            count = self.queryset.filter(tipo_documento=tipo_code).count()
            tipos_stats[tipo_code] = {
                'nombre': tipo_name,
                'total': count
            }
        
        stats = {
            'resumen': {
                'total_documentos': total_documentos,
                'documentos_verificados': documentos_verificados,
                'documentos_pendientes': documentos_pendientes,
                'documentos_rechazados': documentos_rechazados,
                'porcentaje_verificados': round(
                    (documentos_verificados / total_documentos * 100) if total_documentos > 0 else 0, 
                    2
                )
            },
            'por_tipo': tipos_stats,
            'ultima_actualizacion': timezone.now().isoformat()
        }
        
        return Response(stats)