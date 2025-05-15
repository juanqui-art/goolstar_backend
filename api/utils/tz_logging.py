"""
Utilidades de logging específicas para manejo de zonas horarias en GoolStar.

Este módulo complementa logging_utils.py para añadir funcionalidad específica
de registro de eventos relacionados con operaciones de fechas y zonas horarias.
"""
import logging
import functools
from api.utils.date_utils import get_today_date, date_to_datetime

def get_tz_logger(name):
    """
    Obtiene un logger especializado para operaciones con zonas horarias.
    
    Args:
        name: Nombre del módulo, generalmente __name__
        
    Returns:
        Un objeto logger configurado
    """
    return logging.getLogger(f"{name}.timezone")

def log_timezone_operation(logger):
    """
    Decorador para registrar operaciones de conversión/manipulación de zonas horarias.
    
    Args:
        logger: Objeto logger a utilizar
    
    Returns:
        Decorador configurado
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Registrar la llamada a la función
            logger.debug(
                f"TZ Operation: {func.__name__} - Args: {args}, Kwargs: {kwargs}"
            )
            
            try:
                # Ejecutar la función
                result = func(*args, **kwargs)
                
                # Verificar si el resultado es un objeto relacionado con fechas (date o datetime)
                from datetime import date, datetime
                if isinstance(result, (date, datetime)):
                    is_aware = hasattr(result, 'tzinfo') and result.tzinfo is not None
                    logger.debug(
                        f"TZ Operation: {func.__name__} - Result: {result} "
                        f"- TZ Aware: {is_aware} "
                        f"- TZ Info: {getattr(result, 'tzinfo', None)}"
                    )
                else:
                    logger.debug(f"TZ Operation: {func.__name__} - Completed")
                
                return result
            
            except Exception as e:
                # Registrar el error
                logger.error(
                    f"TZ Operation: {func.__name__} - Error: {str(e)}",
                    exc_info=True
                )
                # Re-lanzar la excepción
                raise
        
        return wrapper
    
    return decorator

def detect_naive_datetime(obj, logger):
    """
    Detecta objetos datetime sin zona horaria y los registra.
    
    Args:
        obj: Objeto a verificar
        logger: Logger para registrar el resultado
    
    Returns:
        True si es un datetime sin zona horaria, False en caso contrario
    """
    from datetime import datetime
    
    if isinstance(obj, datetime):
        is_naive = obj.tzinfo is None or obj.tzinfo.utcoffset(obj) is None
        if is_naive:
            import traceback
            stack = traceback.format_stack()[:-1]  # Excluir la llamada actual
            logger.warning(
                f"Naive Datetime Detected: {obj} - "
                f"This could cause timezone issues. "
                f"Location: {stack[-2].strip() if len(stack) > 1 else 'Unknown'}"
            )
            return True
    return False

def log_date_conversion(original_date, converted_datetime, logger):
    """
    Registra conversiones entre tipos date y datetime.
    
    Args:
        original_date: Fecha original (normalmente un objeto date)
        converted_datetime: Fecha convertida (normalmente un datetime con timezone)
        logger: Logger para registrar la conversión
    """
    logger.debug(
        f"Date Conversion: {original_date} ({type(original_date).__name__}) -> "
        f"{converted_datetime} ({type(converted_datetime).__name__}) - "
        f"TZ Info: {getattr(converted_datetime, 'tzinfo', None)}"
    )
