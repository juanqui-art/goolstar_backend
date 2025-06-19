"""
Tests para la capa de servicios.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock

from api.models.base import Categoria, Torneo
from api.models.participantes import Equipo, Jugador, JugadorDocumento
from api.services import DocumentService, ReportService
from api.services.base_service import ValidationError, BusinessRuleError

User = get_user_model()


class DocumentServiceTests(TestCase):
    """Tests para DocumentService"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.service = DocumentService()
        
        # Crear datos de prueba
        self.categoria = Categoria.objects.create(
            nombre='Sub-20',
            descripcion='Categoría Sub-20'
        )
        
        self.torneo = Torneo.objects.create(
            nombre='Torneo Test',
            categoria=self.categoria,
            fecha_inicio=timezone.now().date()
        )
        
        self.equipo = Equipo.objects.create(
            nombre='Equipo Test',
            categoria=self.categoria,
            torneo=self.torneo
        )
        
        self.jugador = Jugador.objects.create(
            primer_nombre='Juan',
            primer_apellido='Pérez',
            cedula='12345678',
            equipo=self.equipo
        )
        
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
    
    def test_validate_document_upload_success(self):
        """Test validación exitosa de subida de documento"""
        result = self.service.validate_document_upload(
            jugador_id=self.jugador.id,
            tipo_documento='DNI',
            archivo=None  # Archivo mock
        )
        
        self.assertTrue(result['is_valid'])
        self.assertTrue(result['jugador_exists'])
        self.assertFalse(result['has_existing_document'])
        self.assertEqual(len(result['warnings']), 0)
    
    def test_validate_document_upload_jugador_not_found(self):
        """Test validación falla cuando jugador no existe"""
        with self.assertRaises(ValidationError) as context:
            self.service.validate_document_upload(
                jugador_id=99999,
                tipo_documento='DNI',
                archivo=None
            )
        
        self.assertEqual(context.exception.error_code, 'JUGADOR_NOT_FOUND')
    
    def test_validate_document_upload_existing_document(self):
        """Test validación con documento existente"""
        # Crear documento existente
        JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test.jpg'
        )
        
        result = self.service.validate_document_upload(
            jugador_id=self.jugador.id,
            tipo_documento='DNI',
            archivo=None
        )
        
        self.assertTrue(result['is_valid'])
        self.assertTrue(result['has_existing_document'])
        self.assertEqual(len(result['warnings']), 1)
    
    def test_verify_document_success(self):
        """Test verificación exitosa de documento"""
        # Crear documento pendiente
        documento = JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        )
        
        result = self.service.verify_document(
            document_id=documento.id,
            user=self.user,
            comentarios='Documento válido'
        )
        
        self.assertEqual(result.estado_verificacion, JugadorDocumento.EstadoVerificacion.VERIFICADO)
        self.assertEqual(result.verificado_por, self.user)
    
    def test_verify_document_already_verified(self):
        """Test verificación de documento ya verificado"""
        # Crear documento ya verificado
        documento = JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.VERIFICADO
        )
        
        with self.assertRaises(BusinessRuleError) as context:
            self.service.verify_document(
                document_id=documento.id,
                user=self.user
            )
        
        self.assertEqual(context.exception.error_code, 'ALREADY_VERIFIED')
    
    def test_reject_document_success(self):
        """Test rechazo exitoso de documento"""
        documento = JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        )
        
        result = self.service.reject_document(
            document_id=documento.id,
            user=self.user,
            comentarios='Documento ilegible'
        )
        
        self.assertEqual(result.estado_verificacion, JugadorDocumento.EstadoVerificacion.RECHAZADO)
    
    def test_reject_document_no_comments(self):
        """Test rechazo falla sin comentarios"""
        documento = JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test.jpg'
        )
        
        with self.assertRaises(ValidationError) as context:
            self.service.reject_document(
                document_id=documento.id,
                user=self.user,
                comentarios=''
            )
        
        self.assertEqual(context.exception.error_code, 'COMMENTS_REQUIRED')
    
    def test_get_documents_statistics(self):
        """Test obtención de estadísticas de documentos"""
        # Crear documentos de prueba
        JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test1.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.VERIFICADO
        )
        
        JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='CEDULA',
            archivo_documento='test2.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        )
        
        stats = self.service.get_documents_statistics()
        
        self.assertEqual(stats['resumen']['total_documentos'], 2)
        self.assertEqual(stats['resumen']['documentos_verificados'], 1)
        self.assertEqual(stats['resumen']['documentos_pendientes'], 1)
        self.assertEqual(stats['resumen']['porcentaje_verificados'], 50.0)
    
    def test_get_documents_by_player(self):
        """Test obtención de documentos por jugador"""
        # Crear documentos de prueba
        doc1 = JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test1.jpg'
        )
        
        doc2 = JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='CEDULA',
            archivo_documento='test2.jpg'
        )
        
        documentos = self.service.get_documents_by_player(self.jugador.id)
        
        self.assertEqual(len(documentos), 2)
        self.assertIn(doc1, documentos)
        self.assertIn(doc2, documentos)
    
    def test_get_pending_documents(self):
        """Test obtención de documentos pendientes"""
        # Crear documentos con diferentes estados
        JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='DNI',
            archivo_documento='test1.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.PENDIENTE
        )
        
        JugadorDocumento.objects.create(
            jugador=self.jugador,
            tipo_documento='CEDULA',
            archivo_documento='test2.jpg',
            estado_verificacion=JugadorDocumento.EstadoVerificacion.VERIFICADO
        )
        
        pendientes = self.service.get_pending_documents()
        
        self.assertEqual(len(pendientes), 1)
        self.assertEqual(pendientes[0].estado_verificacion, JugadorDocumento.EstadoVerificacion.PENDIENTE)


class ReportServiceTests(TestCase):
    """Tests para ReportService"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.service = ReportService()
        
        # Crear datos de prueba
        self.categoria = Categoria.objects.create(
            nombre='Sub-20',
            descripcion='Categoría Sub-20',
            costo_inscripcion=100000
        )
        
        self.torneo = Torneo.objects.create(
            nombre='Torneo Test',
            categoria=self.categoria,
            fecha_inicio=timezone.now().date()
        )
        
        self.equipo = Equipo.objects.create(
            nombre='Equipo Test',
            categoria=self.categoria,
            torneo=self.torneo
        )
    
    def test_get_team_financial_summary_success(self):
        """Test obtención exitosa de resumen financiero"""
        summary = self.service.get_team_financial_summary(self.equipo.id)
        
        self.assertEqual(summary['equipo']['id'], self.equipo.id)
        self.assertEqual(summary['equipo']['nombre'], self.equipo.nombre)
        self.assertIn('balance', summary)
        self.assertIn('fecha_calculo', summary)
    
    def test_get_team_financial_summary_equipo_not_found(self):
        """Test resumen financiero falla con equipo inexistente"""
        with self.assertRaises(ValidationError) as context:
            self.service.get_team_financial_summary(99999)
        
        self.assertEqual(context.exception.error_code, 'EQUIPO_NOT_FOUND')
    
    @patch('api.services.report_service.get_template')
    @patch('api.services.report_service.pisa.pisaDocument')
    def test_generate_players_list_pdf_success(self, mock_pisa, mock_get_template):
        """Test generación exitosa de PDF de lista de jugadores"""
        # Mock del template y PDF
        mock_template = MagicMock()
        mock_template.render.return_value = '<html>Test</html>'
        mock_get_template.return_value = mock_template
        
        mock_pdf = MagicMock()
        mock_pdf.err = False
        mock_pisa.return_value = mock_pdf
        
        # Crear jugador de prueba
        Jugador.objects.create(
            primer_nombre='Juan',
            primer_apellido='Pérez',
            cedula='12345678',
            equipo=self.equipo,
            numero_dorsal=10
        )
        
        response = self.service.generate_players_list_pdf(self.equipo.id)
        
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        mock_get_template.assert_called_once()
    
    @patch('api.services.report_service.get_template')
    @patch('api.services.report_service.pisa.pisaDocument')
    def test_generate_pdf_error(self, mock_pisa, mock_get_template):
        """Test manejo de error en generación de PDF"""
        # Mock del template
        mock_template = MagicMock()
        mock_template.render.return_value = '<html>Test</html>'
        mock_get_template.return_value = mock_template
        
        # Mock PDF con error
        mock_pdf = MagicMock()
        mock_pdf.err = True
        mock_pisa.return_value = mock_pdf
        
        with self.assertRaises(BusinessRuleError) as context:
            self.service.generate_players_list_pdf(self.equipo.id)
        
        self.assertEqual(context.exception.error_code, 'PDF_GENERATION_ERROR')