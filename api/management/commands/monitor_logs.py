"""
Comando Django para monitorear logs y enviar alertas.

Este comando puede configurarse para ejecutarse de forma programada y enviar
alertas por email cuando se detecten problemas en los logs del sistema.
"""
import logging
import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail
from api.utils.log_analyzer import LogAnalyzer
from api.utils.date_utils import get_today_date
from api.utils.tz_logging import log_timezone_operation


class Command(BaseCommand):
    help = 'Monitorea archivos de log y envía alertas cuando detecta problemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Número de días hacia atrás a analizar'
        )
        parser.add_argument(
            '--email',
            action='store_true',
            help='Enviar alertas por email'
        )
        parser.add_argument(
            '--recipients',
            type=str,
            help='Lista de destinatarios separados por coma'
        )
        parser.add_argument(
            '--error-threshold',
            type=int,
            default=5,
            help='Umbral de errores para enviar alertas'
        )
        parser.add_argument(
            '--timezone-threshold',
            type=int,
            default=1,
            help='Umbral de problemas de zona horaria para enviar alertas'
        )

    @log_timezone_operation(logging.getLogger('api.management.commands'))
    def handle(self, *args, **options):
        """
        Ejecuta el comando.
        """
        days = options['days']
        email_enabled = options['email']
        recipients = options.get('recipients', '')
        error_threshold = options['error_threshold']
        timezone_threshold = options['timezone_threshold']

        if email_enabled and not recipients:
            recipients = ','.join([admin[1] for admin in settings.ADMINS])

        # Iniciar el análisis
        self.stdout.write(self.style.SUCCESS(f'Analizando logs de los últimos {days} días...'))

        analyzer = LogAnalyzer()
        report = analyzer.generate_report(days_back=days)
        naive_datetime_issues = report.get('naive_datetimes', [])

        today = get_today_date()
        errors = []

        # Analizar logs de error
        error_count = 0
        if 'file_analysis' in report and 'error.log' in report['file_analysis']:
            error_analysis = report['file_analysis']['error.log']
            error_count = error_analysis.get('total_entries', 0)

            # Extraer los errores más comunes para el reporte
            if 'common_errors' in error_analysis:
                for error in error_analysis['common_errors']:
                    errors.append({
                        'message': error['error'],
                        'count': error['count']
                    })

        # Resumen para mostrar
        self.stdout.write("=== RESUMEN DEL ANÁLISIS ===")
        self.stdout.write(f"Total errores encontrados: {error_count}")
        self.stdout.write(f"Problemas de zona horaria: {len(naive_datetime_issues)}")

        # Determinar si es necesario enviar alertas
        should_alert = False
        alert_reasons = []

        if error_count >= error_threshold:
            should_alert = True
            alert_reasons.append(f"Se encontraron {error_count} errores (umbral: {error_threshold})")
            self.stdout.write(self.style.WARNING(f'⚠️ Umbral de errores superado: {error_count} >= {error_threshold}'))
        
        if len(naive_datetime_issues) >= timezone_threshold:
            should_alert = True
            alert_reasons.append(f"Se encontraron {len(naive_datetime_issues)} problemas de zona horaria (umbral: {timezone_threshold})")
            self.stdout.write(self.style.WARNING(f'⚠️ Umbral de problemas de zona horaria superado: {len(naive_datetime_issues)} >= {timezone_threshold}'))

        # Enviar email si es necesario
        if should_alert and email_enabled and recipients:
            recipient_list = [email.strip() for email in recipients.split(',')]
            
            # Construir el contenido del email
            subject = f'[GoolStar] Alerta: Problemas detectados en los logs - {today}'
            
            message = "Se han detectado los siguientes problemas en los logs de GoolStar:\n\n"
            for reason in alert_reasons:
                message += f"- {reason}\n"
            
            message += "\n=== Detalle de errores más comunes ===\n"
            for error in errors[:5]:  # Mostrar los 5 errores más comunes
                message += f"- {error['message']} ({error['count']} ocurrencias)\n"
            
            if naive_datetime_issues:
                message += "\n=== Ejemplos de problemas con fechas ===\n"
                for issue in naive_datetime_issues[:3]:  # Mostrar hasta 3 ejemplos
                    message += f"- {issue['timestamp']}: {issue['message']}\n"
                    message += f"  En archivo: {issue['file']} (línea {issue['line']})\n"
            
            message += "\nEste mensaje ha sido generado automáticamente por el sistema de monitoreo de logs de GoolStar."
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,
                )
                self.stdout.write(self.style.SUCCESS(f'✅ Alerta enviada a {", ".join(recipient_list)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error al enviar email: {str(e)}'))
        
        elif should_alert:
            self.stdout.write(self.style.WARNING('⚠️ Se deben enviar alertas, pero el envío por email no está habilitado'))
        
        else:
            self.stdout.write(self.style.SUCCESS('✅ No se detectaron problemas que requieran alertas'))
        
        return 0
