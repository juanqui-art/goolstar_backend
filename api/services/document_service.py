"""
Servicio para manejo de documentos de jugadores.
Encapsula toda la lógica de negocio relacionada con validación, verificación y gestión de documentos.
"""

from typing import Dict, List, Any

from django.contrib.auth import get_user_model
from django.db import transaction

from .base_service import BaseService, ValidationError, BusinessRuleError
from ..models.participantes import JugadorDocumento, Jugador

User = get_user_model()


class DocumentService(BaseService):
    """
    Servicio para gestión de documentos de jugadores.
    
    Responsabilidades:
    - Validación de documentos
    - Verificación y rechazo de documentos
    - Estadísticas de documentos
    - Lógica de negocio para subida de archivos
    """

    def __init__(self):
        super().__init__()

    def validate_document_upload(self, jugador_id: int, tipo_documento: str, archivo) -> Dict[str, Any]:
        """
        Valida que un documento pueda ser subido.
        
        Args:
            jugador_id: ID del jugador
            tipo_documento: Tipo de documento (DNI, CEDULA, etc.)
            archivo: Archivo a subir
            
        Returns:
            Dict con resultado de validación
            
        Raises:
            ValidationError: Si la validación falla
        """
        self.log_operation("validate_document_upload", {
            "jugador_id": jugador_id,
            "tipo_documento": tipo_documento
        })

        try:
            # Verificar que el jugador existe
            if not Jugador.objects.filter(id=jugador_id).exists():
                raise ValidationError(
                    "Jugador no encontrado",
                    error_code="JUGADOR_NOT_FOUND",
                    details={"jugador_id": jugador_id}
                )

            # Verificar si ya existe un documento del mismo tipo para este jugador
            existing_doc = JugadorDocumento.objects.filter(
                jugador_id=jugador_id,
                tipo_documento=tipo_documento
            ).first()

            validation_result = {
                "is_valid": True,
                "jugador_exists": True,
                "has_existing_document": existing_doc is not None,
                "existing_document_id": existing_doc.id if existing_doc else None,
                "warnings": []
            }

            if existing_doc:
                validation_result["warnings"].append(
                    f"Ya existe un documento {tipo_documento} para este jugador. "
                    f"El nuevo documento reemplazará al anterior."
                )

            return validation_result

        except Exception as e:
            self.log_error("validate_document_upload", e, {
                "jugador_id": jugador_id,
                "tipo_documento": tipo_documento
            })
            raise

    @transaction.atomic
    def verify_document(self, document_id: int, user: User, comentarios: str = "") -> JugadorDocumento:
        """
        Verifica un documento como válido.
        
        Args:
            document_id: ID del documento
            user: Usuario que verifica
            comentarios: Comentarios de verificación
            
        Returns:
            Documento verificado
            
        Raises:
            ValidationError: Si el documento no se puede verificar
        """
        self.log_operation("verify_document", {
            "document_id": document_id,
            "user_id": user.id,
            "has_comments": bool(comentarios)
        })

        try:
            documento = JugadorDocumento.objects.select_related('jugador').get(id=document_id)

            # Verificar que el documento esté en estado pendiente
            if documento.estado_verificacion == JugadorDocumento.EstadoVerificacion.VERIFICADO:
                raise BusinessRuleError(
                    "El documento ya está verificado",
                    error_code="ALREADY_VERIFIED"
                )

            # Marcar como verificado usando el método del modelo
            documento.marcar_como_verificado(user, comentarios)

            self.log_operation("document_verified", {
                "document_id": document_id,
                "jugador": str(documento.jugador),
                "tipo": documento.tipo_documento
            })

            return documento

        except JugadorDocumento.DoesNotExist:
            raise ValidationError(
                "Documento no encontrado",
                error_code="DOCUMENT_NOT_FOUND",
                details={"document_id": document_id}
            )
        except Exception as e:
            self.log_error("verify_document", e, {"document_id": document_id})
            raise

    @transaction.atomic
    def reject_document(self, document_id: int, user: User, comentarios: str) -> JugadorDocumento:
        """
        Rechaza un documento con comentarios obligatorios.
        
        Args:
            document_id: ID del documento
            user: Usuario que rechaza
            comentarios: Comentarios de rechazo (obligatorios)
            
        Returns:
            Documento rechazado
            
        Raises:
            ValidationError: Si los comentarios están vacíos o el documento no existe
        """
        if not comentarios or not comentarios.strip():
            raise ValidationError(
                "Los comentarios son obligatorios para rechazar un documento",
                error_code="COMMENTS_REQUIRED"
            )

        self.log_operation("reject_document", {
            "document_id": document_id,
            "user_id": user.id,
            "comments_length": len(comentarios)
        })

        try:
            documento = JugadorDocumento.objects.select_related('jugador').get(id=document_id)

            # Verificar que el documento no esté ya rechazado
            if documento.estado_verificacion == JugadorDocumento.EstadoVerificacion.RECHAZADO:
                raise BusinessRuleError(
                    "El documento ya está rechazado",
                    error_code="ALREADY_REJECTED"
                )

            # Rechazar usando el método del modelo
            documento.rechazar_documento(user, comentarios)

            self.log_operation("document_rejected", {
                "document_id": document_id,
                "jugador": str(documento.jugador),
                "tipo": documento.tipo_documento
            })

            return documento

        except JugadorDocumento.DoesNotExist:
            raise ValidationError(
                "Documento no encontrado",
                error_code="DOCUMENT_NOT_FOUND",
                details={"document_id": document_id}
            )
        except Exception as e:
            self.log_error("reject_document", e, {"document_id": document_id})
            raise

    def get_documents_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales de documentos.
        
        Returns:
            Dict con estadísticas completas
        """
        self.log_operation("get_documents_statistics")

        try:
            queryset = JugadorDocumento.objects.all()

            total_documentos = queryset.count()
            documentos_verificados = queryset.filter(
                estado_verificacion=JugadorDocumento.EstadoVerificacion.VERIFICADO
            ).count()
            documentos_pendientes = queryset.filter(
                estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
            ).count()
            documentos_rechazados = queryset.filter(
                estado_verificacion=JugadorDocumento.EstadoVerificacion.RECHAZADO
            ).count()

            # Estadísticas por tipo de documento
            tipos_stats = {}
            for tipo_choice in JugadorDocumento.TipoDocumento.choices:
                tipo_code, tipo_name = tipo_choice
                count = queryset.filter(tipo_documento=tipo_code).count()
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
                'ultima_actualizacion': self.get_current_timestamp().isoformat()
            }

            return stats

        except Exception as e:
            self.log_error("get_documents_statistics", e)
            raise

    def get_documents_by_player(self, jugador_id: int) -> List[JugadorDocumento]:
        """
        Obtiene todos los documentos de un jugador específico.
        
        Args:
            jugador_id: ID del jugador
            
        Returns:
            Lista de documentos del jugador
            
        Raises:
            ValidationError: Si el jugador no existe
        """
        self.log_operation("get_documents_by_player", {"jugador_id": jugador_id})

        try:
            # Verificar que el jugador existe
            if not Jugador.objects.filter(id=jugador_id).exists():
                raise ValidationError(
                    "Jugador no encontrado",
                    error_code="JUGADOR_NOT_FOUND",
                    details={"jugador_id": jugador_id}
                )

            documentos = JugadorDocumento.objects.filter(
                jugador_id=jugador_id
            ).select_related('jugador').order_by('-fecha_subida')

            return list(documentos)

        except Exception as e:
            self.log_error("get_documents_by_player", e, {"jugador_id": jugador_id})
            raise

    def get_pending_documents(self) -> List[JugadorDocumento]:
        """
        Obtiene documentos pendientes de verificación.
        
        Returns:
            Lista de documentos pendientes
        """
        self.log_operation("get_pending_documents")

        try:
            documentos_pendientes = JugadorDocumento.objects.filter(
                estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
            ).select_related('jugador').order_by('-fecha_subida')

            return list(documentos_pendientes)

        except Exception as e:
            self.log_error("get_pending_documents", e)
            raise
