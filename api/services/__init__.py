"""
Services layer para la aplicación GoolStar.

Esta capa contiene la lógica de negocio extraída de views y models,
organizando el código en servicios especializados por dominio.

Patrones utilizados:
- Service Layer Pattern: Encapsula lógica de negocio
- Dependency Injection: Servicios pueden ser fácilmente testeados
- Single Responsibility: Cada servicio tiene una responsabilidad específica
"""

# Imports de servicios para fácil acceso
from .base_service import BaseService, ServiceException, ValidationError, BusinessRuleError
from .document_service import DocumentService
from .report_service import ReportService

__all__ = [
    'BaseService',
    'ServiceException', 
    'ValidationError',
    'BusinessRuleError',
    'DocumentService',
    'ReportService',
]