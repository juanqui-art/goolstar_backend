"""
Servicio para generación de reportes y PDFs.
Encapsula toda la lógica de generación de documentos y reportes del sistema.
"""

from decimal import Decimal
from io import BytesIO
from typing import Dict, Any

from django.db import models
from django.http import HttpResponse
from django.template.loader import get_template
from django.utils import timezone
from xhtml2pdf import pisa

from .base_service import BaseService, ValidationError, BusinessRuleError
from ..models.competicion import Partido, Tarjeta
from ..models.financiero import TransaccionPago
from ..models.participantes import Equipo


class ReportService(BaseService):
    """
    Servicio para generación de reportes y PDFs.
    
    Responsabilidades:
    - Generación de PDFs de listas de jugadores
    - Reportes de historial de partidos
    - Balances financieros de equipos
    - Reportes estadísticos
    """

    def __init__(self):
        super().__init__()

    def _generate_pdf_from_html(self, html: str, filename: str) -> HttpResponse:
        """
        Genera un PDF a partir de HTML y retorna HttpResponse.
        
        Args:
            html: Contenido HTML
            filename: Nombre del archivo
            
        Returns:
            HttpResponse con el PDF
            
        Raises:
            BusinessRuleError: Si hay error generando el PDF
        """
        try:
            result = BytesIO()
            pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

            if pdf.err:
                raise BusinessRuleError(
                    "Error al generar PDF",
                    error_code="PDF_GENERATION_ERROR"
                )

            response = HttpResponse(result.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        except Exception as e:
            self.log_error("_generate_pdf_from_html", e, {"filename": filename})
            raise

    def generate_players_list_pdf(self, equipo_id: int) -> HttpResponse:
        """
        Genera PDF con la lista de jugadores de un equipo.
        
        Args:
            equipo_id: ID del equipo
            
        Returns:
            HttpResponse con el PDF
            
        Raises:
            ValidationError: Si el equipo no existe
        """
        self.log_operation("generate_players_list_pdf", {"equipo_id": equipo_id})

        try:
            equipo = Equipo.objects.select_related('categoria', 'torneo').get(id=equipo_id)
        except Equipo.DoesNotExist:
            raise ValidationError(
                "Equipo no encontrado",
                error_code="EQUIPO_NOT_FOUND",
                details={"equipo_id": equipo_id}
            )

        try:
            # Obtener jugadores del equipo optimizado
            jugadores = equipo.jugadores.select_related('equipo').all().order_by('numero_dorsal')

            # Preparar contexto para la plantilla
            context = {
                'equipo': equipo,
                'jugadores': jugadores,
                'fecha_actual': timezone.now().date(),
                'total_jugadores': jugadores.count(),
            }

            # Renderizar plantilla a HTML
            template = get_template('admin/equipos/lista_jugadores_pdf.html')
            html = template.render(context)

            # Generar filename
            filename = f"Lista_Jugadores_{equipo.nombre}_{timezone.now().strftime('%Y%m%d')}.pdf"

            self.log_operation("players_list_pdf_generated", {
                "equipo": equipo.nombre,
                "total_jugadores": jugadores.count()
            })

            return self._generate_pdf_from_html(html, filename)

        except Exception as e:
            self.log_error("generate_players_list_pdf", e, {"equipo_id": equipo_id})
            raise

    def generate_match_history_pdf(self, equipo_id: int) -> HttpResponse:
        """
        Genera PDF con el historial de partidos de un equipo.
        
        Args:
            equipo_id: ID del equipo
            
        Returns:
            HttpResponse con el PDF
            
        Raises:
            ValidationError: Si el equipo no existe
        """
        self.log_operation("generate_match_history_pdf", {"equipo_id": equipo_id})

        try:
            equipo = Equipo.objects.select_related('categoria', 'torneo').get(id=equipo_id)
        except Equipo.DoesNotExist:
            raise ValidationError(
                "Equipo no encontrado",
                error_code="EQUIPO_NOT_FOUND",
                details={"equipo_id": equipo_id}
            )

        try:
            # Obtener todos los partidos donde participó el equipo (como local o visitante)
            partidos = Partido.objects.filter(
                models.Q(equipo_1=equipo) | models.Q(equipo_2=equipo)
            ).select_related(
                'equipo_1', 'equipo_2', 'jornada', 'torneo', 'arbitro', 'fase_eliminatoria'
            ).order_by('fecha')

            # Preparar contexto para la plantilla
            context = {
                'equipo': equipo,
                'partidos': partidos,
                'fecha_actual': timezone.now().date(),
                'total_partidos': partidos.count(),
            }

            # Renderizar plantilla a HTML
            template = get_template('admin/equipos/historial_partidos_pdf.html')
            html = template.render(context)

            # Generar filename
            filename = f"Historial_Partidos_{equipo.nombre}_{timezone.now().strftime('%Y%m%d')}.pdf"

            self.log_operation("match_history_pdf_generated", {
                "equipo": equipo.nombre,
                "total_partidos": partidos.count()
            })

            return self._generate_pdf_from_html(html, filename)

        except Exception as e:
            self.log_error("generate_match_history_pdf", e, {"equipo_id": equipo_id})
            raise

    def generate_financial_balance_pdf(self, equipo_id: int) -> HttpResponse:
        """
        Genera PDF con el balance financiero de un equipo.
        
        Args:
            equipo_id: ID del equipo
            
        Returns:
            HttpResponse con el PDF
            
        Raises:
            ValidationError: Si el equipo no existe
        """
        self.log_operation("generate_financial_balance_pdf", {"equipo_id": equipo_id})

        try:
            equipo = Equipo.objects.select_related('categoria', 'torneo').get(id=equipo_id)
        except Equipo.DoesNotExist:
            raise ValidationError(
                "Equipo no encontrado",
                error_code="EQUIPO_NOT_FOUND",
                details={"equipo_id": equipo_id}
            )

        try:
            # Calcular balance financiero
            balance_data = self._calculate_team_financial_balance(equipo)

            # Preparar contexto para la plantilla
            context = {
                'equipo': equipo,
                'fecha_actual': timezone.now(),
                **balance_data  # Expandir todos los datos del balance
            }

            # Renderizar plantilla a HTML
            template = get_template('admin/balance_equipo_pdf.html')
            html = template.render(context)

            # Generar filename
            filename = f"Balance_Financiero_{equipo.nombre}_{timezone.now().strftime('%Y%m%d')}.pdf"

            self.log_operation("financial_balance_pdf_generated", {
                "equipo": equipo.nombre,
                "deuda_total": balance_data['deuda_total']
            })

            return self._generate_pdf_from_html(html, filename)

        except Exception as e:
            self.log_error("generate_financial_balance_pdf", e, {"equipo_id": equipo_id})
            raise

    def _calculate_team_financial_balance(self, equipo: Equipo) -> Dict[str, Any]:
        """
        Calcula el balance financiero de un equipo.
        
        Args:
            equipo: Instancia del equipo
            
        Returns:
            Dict con datos del balance financiero
        """
        self.log_operation("calculate_team_financial_balance", {"equipo_id": equipo.id})

        try:
            # Obtener datos de inscripción
            costo_inscripcion = equipo.categoria.costo_inscripcion or Decimal('0.00')
            abonos_inscripcion = TransaccionPago.objects.filter(
                equipo=equipo,
                tipo='abono_inscripcion'
            ).aggregate(total=models.Sum('monto'))['total'] or Decimal('0.00')
            saldo_inscripcion = costo_inscripcion - abonos_inscripcion

            # Obtener tarjetas pendientes de pago optimizado
            tarjetas_pendientes = Tarjeta.objects.filter(
                jugador__equipo=equipo,
                pagada=False
            ).select_related('jugador', 'partido', 'jugador__equipo')

            # Separar por tipo usando filtrado en Python para evitar queries adicionales
            tarjetas_amarillas = [t for t in tarjetas_pendientes if t.tipo == 'AMARILLA']
            tarjetas_rojas = [t for t in tarjetas_pendientes if t.tipo == 'ROJA']

            # Calcular totales
            total_amarillas = sum(t.monto_multa for t in tarjetas_amarillas)
            total_rojas = sum(t.monto_multa for t in tarjetas_rojas)
            deuda_total = saldo_inscripcion + total_amarillas + total_rojas

            return {
                'costo_inscripcion': costo_inscripcion,
                'abonos_inscripcion': abonos_inscripcion,
                'saldo_inscripcion': saldo_inscripcion,
                'tarjetas_amarillas': tarjetas_amarillas,
                'tarjetas_rojas': tarjetas_rojas,
                'total_amarillas': total_amarillas,
                'total_rojas': total_rojas,
                'deuda_total': deuda_total,
                'tiene_deudas': deuda_total > 0,
            }

        except Exception as e:
            self.log_error("_calculate_team_financial_balance", e, {"equipo_id": equipo.id})
            raise

    def get_team_financial_summary(self, equipo_id: int) -> Dict[str, Any]:
        """
        Obtiene resumen financiero de un equipo sin generar PDF.
        
        Args:
            equipo_id: ID del equipo
            
        Returns:
            Dict con resumen financiero
            
        Raises:
            ValidationError: Si el equipo no existe
        """
        self.log_operation("get_team_financial_summary", {"equipo_id": equipo_id})

        try:
            equipo = Equipo.objects.select_related('categoria').get(id=equipo_id)
        except Equipo.DoesNotExist:
            raise ValidationError(
                "Equipo no encontrado",
                error_code="EQUIPO_NOT_FOUND",
                details={"equipo_id": equipo_id}
            )

        try:
            balance_data = self._calculate_team_financial_balance(equipo)

            # Agregar información del equipo
            summary = {
                'equipo': {
                    'id': equipo.id,
                    'nombre': equipo.nombre,
                    'categoria': equipo.categoria.nombre,
                },
                'balance': balance_data,
                'fecha_calculo': timezone.now().isoformat()
            }

            return summary

        except Exception as e:
            self.log_error("get_team_financial_summary", e, {"equipo_id": equipo_id})
            raise
