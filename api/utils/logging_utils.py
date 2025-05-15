"""
Utilidades para logging en el proyecto GoolStar.

Este módulo proporciona funciones y decoradores para facilitar
el uso consistente de logging en todo el proyecto.
"""
import logging
import time
import functools
import traceback
from django.conf import settings

# Constantes para el formato de logs
LOG_FORMAT = '{asctime} [{levelname}] {name} {filename}:{lineno:d} {message}'

def get_logger(name):
    """
    Obtiene un logger configurado para el módulo especificado.
    
    Args:
        name: Nombre del módulo, generalmente __name__
        
    Returns:
        Un objeto logger configurado
    """
    return logging.getLogger(name)

def log_api_request(logger):
    """
    Decorador para registrar información sobre las solicitudes API.
    
    Args:
        logger: Objeto logger a utilizar
    
    Returns:
        Decorador configurado
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            start_time = time.time()
            
            # Registrar la solicitud entrante
            logger.info(
                f"API Request: {request.method} {request.path} "
                f"from {request.META.get('REMOTE_ADDR')} "
                f"- User: {request.user}"
            )
            
            # Añadir información de parámetros si está en modo debug
            if settings.DEBUG:
                logger.debug(
                    f"Request Params: GET={request.GET}, POST={request.POST}, "
                    f"FILES={bool(request.FILES)}, DATA={getattr(request, 'data', {})}"
                )
            
            try:
                # Ejecutar la vista
                response = view_func(self, request, *args, **kwargs)
                
                # Registrar el tiempo de respuesta
                duration = time.time() - start_time
                logger.info(
                    f"API Response: {request.method} {request.path} "
                    f"- Status: {getattr(response, 'status_code', 'unknown')} "
                    f"- Duration: {duration:.2f}s"
                )
                
                return response
            
            except Exception as e:
                # Registrar la excepción con detalles
                duration = time.time() - start_time
                logger.error(
                    f"API Error: {request.method} {request.path} "
                    f"- Exception: {str(e)} "
                    f"- Duration: {duration:.2f}s\n"
                    f"{traceback.format_exc()}"
                )
                # Re-lanzar la excepción para que sea manejada por Django
                raise
        
        return wrapper
    
    return decorator

def log_db_operation(logger):
    """
    Decorador para registrar información sobre operaciones de base de datos.
    
    Args:
        logger: Objeto logger a utilizar
    
    Returns:
        Decorador configurado
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Registrar el inicio de la operación
            logger.debug(f"DB Operation: {func.__name__} - Starting")
            
            try:
                # Ejecutar la función
                result = func(*args, **kwargs)
                
                # Registrar el éxito
                duration = time.time() - start_time
                logger.debug(
                    f"DB Operation: {func.__name__} - Completed "
                    f"- Duration: {duration:.2f}s"
                )
                
                return result
            
            except Exception as e:
                # Registrar el error
                duration = time.time() - start_time
                logger.error(
                    f"DB Operation: {func.__name__} - Failed "
                    f"- Exception: {str(e)} "
                    f"- Duration: {duration:.2f}s\n"
                    f"{traceback.format_exc()}"
                )
                # Re-lanzar la excepción
                raise
        
        return wrapper
    
    return decorator
