"""
Validadores personalizados para archivos de documentos de jugadores.
Implementa las mejores prácticas de seguridad para validación de archivos.
"""

import magic
import mimetypes
import os
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class DocumentFileValidator:
    """
    Validador comprehensivo para documentos de jugadores.
    Implementa múltiples capas de validación de seguridad.
    """
    
    # Tipos MIME permitidos (whitelist de seguridad)
    ALLOWED_MIME_TYPES = [
        'image/jpeg',
        'image/png', 
        'application/pdf',
    ]
    
    # Extensiones permitidas (backup de seguridad)
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf']
    
    # Tamaño máximo de archivo (5MB)
    MAX_FILE_SIZE = getattr(settings, 'CLOUDINARY_MAX_FILE_SIZE', 5 * 1024 * 1024)
    
    def __init__(self, allowed_extensions=None, max_file_size=None):
        """
        Inicializar validador con parámetros opcionales.
        
        Args:
            allowed_extensions: Lista de extensiones permitidas
            max_file_size: Tamaño máximo en bytes
        """
        if allowed_extensions is not None:
            self.allowed_extensions = allowed_extensions
        else:
            self.allowed_extensions = self.ALLOWED_EXTENSIONS
            
        if max_file_size is not None:
            self.max_file_size = max_file_size
        else:
            self.max_file_size = self.MAX_FILE_SIZE
    
    def __call__(self, file):
        """
        Ejecutar validación completa del archivo.
        
        Args:
            file: Archivo a validar
            
        Raises:
            ValidationError: Si el archivo no pasa las validaciones
        """
        # 1. Validar tamaño de archivo
        self._validate_file_size(file)
        
        # 2. Validar extensión de archivo
        self._validate_file_extension(file)
        
        # 3. Validar contenido MIME real (seguridad crítica)
        self._validate_mime_type(file)
        
        # 4. Validar nombre de archivo (seguridad)
        self._validate_filename(file)
    
    def _validate_file_size(self, file):
        """Validar que el archivo no exceda el tamaño máximo."""
        if file.size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            raise ValidationError(
                f'El archivo es demasiado grande. Tamaño máximo permitido: {max_size_mb:.1f}MB'
            )
    
    def _validate_file_extension(self, file):
        """Validar extensión del archivo."""
        filename = file.name.lower()
        extension = os.path.splitext(filename)[1]
        
        if extension not in [ext.lower() for ext in self.allowed_extensions]:
            allowed_formats = ', '.join(self.allowed_extensions)
            raise ValidationError(
                f'Formato de archivo no permitido. Formatos permitidos: {allowed_formats}'
            )
    
    def _validate_mime_type(self, file):
        """
        Validar tipo MIME real del archivo usando python-magic.
        Esta es la validación de seguridad más importante.
        """
        try:
            # Leer una muestra del archivo para determinar el tipo MIME real
            file.seek(0)
            file_content = file.read(2048)  # Leer primeros 2KB
            file.seek(0)  # Resetear posición
            
            # Detectar tipo MIME real usando magic
            detected_mime = magic.from_buffer(file_content, mime=True)
            
            # Verificar contra whitelist de tipos permitidos
            if detected_mime not in self.ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f'Tipo de archivo no permitido. El archivo parece ser: {detected_mime}. '
                    f'Tipos permitidos: {", ".join(self.ALLOWED_MIME_TYPES)}'
                )
                
        except Exception as e:
            raise ValidationError(
                f'Error al validar el contenido del archivo: {str(e)}'
            )
    
    def _validate_filename(self, file):
        """
        Validar que el nombre del archivo sea seguro.
        Previene ataques de path traversal y nombres maliciosos.
        """
        filename = file.name
        
        # Verificar caracteres peligrosos
        dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                raise ValidationError(
                    f'Nombre de archivo contiene caracteres no permitidos: {char}'
                )
        
        # Verificar longitud del nombre
        if len(filename) > 255:
            raise ValidationError(
                'Nombre de archivo demasiado largo (máximo 255 caracteres)'
            )
        
        # Verificar que no sea solo espacios o puntos
        if filename.strip().replace('.', '') == '':
            raise ValidationError(
                'Nombre de archivo no válido'
            )


@deconstructible 
class ImageDocumentValidator(DocumentFileValidator):
    """
    Validador específico para imágenes de documentos (DNI, cédula).
    Extiende DocumentFileValidator con validaciones específicas para imágenes.
    """
    
    # Solo imágenes para este validador
    ALLOWED_MIME_TYPES = [
        'image/jpeg',
        'image/png',
    ]
    
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']


@deconstructible
class PDFDocumentValidator(DocumentFileValidator):
    """
    Validador específico para documentos PDF.
    """
    
    # Solo PDF para este validador
    ALLOWED_MIME_TYPES = ['application/pdf']
    ALLOWED_EXTENSIONS = ['.pdf']


def validate_document_file(file):
    """
    Función de conveniencia para validar archivos de documentos.
    Puede ser usada directamente en modelos Django.
    """
    validator = DocumentFileValidator()
    return validator(file)


def validate_image_document(file):
    """
    Función de conveniencia para validar imágenes de documentos.
    """
    validator = ImageDocumentValidator()
    return validator(file)


def validate_pdf_document(file):
    """
    Función de conveniencia para validar documentos PDF.
    """
    validator = PDFDocumentValidator()
    return validator(file)