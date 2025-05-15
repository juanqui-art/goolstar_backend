"""
Middleware para logging de solicitudes HTTP en GoolStar.

Este middleware proporciona un registro completo de todas las solicitudes HTTP
entrantes y salientes, incluyendo información de tiempo de respuesta y errores.
"""
import time
import json
import logging
from django.utils.deprecation import MiddlewareMixin

# Configurar logger específico para el middleware
logger = logging.getLogger('api.middleware.logging')

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware que registra todas las solicitudes HTTP entrantes y salientes.
    Incluye información de tiempo de respuesta y detalles de la solicitud/respuesta.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization
    
    def process_request(self, request):
        """
        Procesa la solicitud entrante y registra información relevante.
        """
        # Añadir timestamp para calcular tiempo de respuesta
        request._logging_start_time = time.time()
        
        # Registrar información básica de la solicitud
        logger.info(
            f"HTTP Request: {request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR')} "
            f"- User: {getattr(request, 'user', 'AnonymousUser')}"
        )
        
        # No devolver nada para permitir que la solicitud continúe
        return None
    
    def process_response(self, request, response):
        """
        Procesa la respuesta saliente y registra información sobre el tiempo de respuesta.
        """
        # Calcular tiempo de respuesta si está disponible
        if hasattr(request, '_logging_start_time'):
            duration = time.time() - request._logging_start_time
            
            # Registrar información de la respuesta
            logger.info(
                f"HTTP Response: {request.method} {request.path} "
                f"- Status: {response.status_code} "
                f"- Duration: {duration:.2f}s "
                f"- Content-Type: {response.get('Content-Type', 'unknown')}"
            )
            
            # Registrar información adicional para respuestas erróneas
            if response.status_code >= 400:
                # Intentar obtener el cuerpo de la respuesta para errores
                content = None
                if hasattr(response, 'content'):
                    try:
                        content = response.content.decode('utf-8')
                        # Si es JSON, intentar formatearlo
                        if response.get('Content-Type', '').startswith('application/json'):
                            content = json.loads(content)
                    except Exception:
                        content = "Error al decodificar contenido de respuesta"
                
                logger.warning(
                    f"HTTP Error Response: {request.method} {request.path} "
                    f"- Status: {response.status_code} "
                    f"- Content: {content}"
                )
        
        return response
    
    def process_exception(self, request, exception):
        """
        Procesa excepciones no manejadas durante el procesamiento de la solicitud.
        """
        logger.error(
            f"HTTP Request Exception: {request.method} {request.path} "
            f"- Exception: {type(exception).__name__}: {str(exception)}",
            exc_info=True
        )
        # No devolver nada para permitir que Django maneje la excepción normalmente
        return None
