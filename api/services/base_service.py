"""
Clase base para servicios de la aplicación.
Proporciona funcionalidades comunes y estructura consistente.
"""

from abc import ABC
from typing import Any, Dict, Optional
from django.utils import timezone
from api.utils.logging_utils import get_logger


class BaseService(ABC):
    """
    Clase base abstracta para todos los servicios.
    
    Proporciona:
    - Logging consistente
    - Manejo de errores estándar
    - Métodos utilitarios comunes
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def log_operation(self, operation: str, details: Optional[Dict[str, Any]] = None):
        """Log de operaciones del servicio"""
        message = f"{operation}"
        if details:
            details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            message += f" - {details_str}"
        
        self.logger.info(message)
    
    def log_error(self, operation: str, error: Exception, details: Optional[Dict[str, Any]] = None):
        """Log de errores del servicio"""
        message = f"Error en {operation}: {str(error)}"
        if details:
            details_str = ", ".join([f"{k}={v}" for k, v in details.items()])
            message += f" - {details_str}"
        
        self.logger.error(message, exc_info=True)
    
    def get_current_timestamp(self):
        """Obtener timestamp actual"""
        return timezone.now()


class ServiceException(Exception):
    """Excepción base para errores de servicios"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(message)


class ValidationError(ServiceException):
    """Error de validación en servicios"""
    pass


class BusinessRuleError(ServiceException):
    """Error de regla de negocio en servicios"""
    pass