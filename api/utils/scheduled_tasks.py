"""
Tareas programadas para el sistema GoolStar con soporte de logging.

Este módulo contiene tareas que pueden ejecutarse periódicamente
para realizar mantenimiento y actualización de datos en el sistema.
"""
import logging
import os
import datetime
from django.conf import settings
from django.utils import timezone
from api.utils.date_utils import get_today_date, date_to_datetime
from api.utils.tz_logging import log_timezone_operation, detect_naive_datetime

# Configurar logger específico para tareas programadas
logger = logging.getLogger('api.scheduled_tasks')

@log_timezone_operation(logger)
def actualizar_estadisticas_diarias():
    """
    Actualiza las estadísticas diarias de todos los torneos activos.
    
    Esta tarea debe programarse para ejecutarse una vez al día.
    """
    from api.models import Torneo, EstadisticaEquipo
    
    logger.info("Iniciando actualización diaria de estadísticas")
    
    # Usar fecha actual con zona horaria correcta
    today = get_today_date()
    today_dt = date_to_datetime(today)
    
    logger.debug(f"Fecha actual para actualización: {today} ({today_dt.tzinfo})")
    
    # Buscar torneos activos
    try:
        torneos_activos = Torneo.objects.filter(
            fecha_inicio__lte=today_dt,
            fecha_fin__gte=today_dt
        ).select_related('categoria')
        
        logger.info(f"Se encontraron {torneos_activos.count()} torneos activos para actualizar")
        
        for torneo in torneos_activos:
            logger.info(f"Actualizando estadísticas para torneo: {torneo.nombre}")
            equipos_actualizados = 0
            
            # Obtener todos los equipos del torneo
            equipos = torneo.equipos.all()
            
            for equipo in equipos:
                try:
                    # Buscar o crear estadísticas
                    estadistica, created = EstadisticaEquipo.objects.get_or_create(
                        equipo=equipo,
                        torneo=torneo
                    )
                    
                    # Actualizar estadísticas
                    estadistica.actualizar()
                    equipos_actualizados += 1
                    
                    if created:
                        logger.info(f"Creadas nuevas estadísticas para equipo: {equipo.nombre}")
                    else:
                        logger.debug(f"Actualizadas estadísticas para equipo: {equipo.nombre}")
                        
                except Exception as e:
                    logger.error(
                        f"Error al actualizar estadísticas para equipo {equipo.nombre}: {str(e)}",
                        exc_info=True
                    )
            
            logger.info(f"Actualizados {equipos_actualizados} equipos para torneo {torneo.nombre}")
                    
    except Exception as e:
        logger.error(f"Error en actualización diaria de estadísticas: {str(e)}", exc_info=True)
        raise
    
    logger.info("Finalizada actualización diaria de estadísticas")
    return True

@log_timezone_operation(logger)
def limpiar_logs_antiguos(dias_antiguedad=30):
    """
    Elimina archivos de log con más de X días de antigüedad.
    
    Args:
        dias_antiguedad: Número de días a partir de los cuales considerar un log como antiguo
    """
    logger.info(f"Iniciando limpieza de logs antiguos (>{dias_antiguedad} días)")
    
    log_dir = settings.LOGS_DIR
    today = get_today_date()
    cutoff_date = today - datetime.timedelta(days=dias_antiguedad)
    
    logger.debug(f"Fecha límite para logs: {cutoff_date}")
    
    try:
        archivos_eliminados = 0
        archivos_rotados = []
        
        for archivo in os.listdir(log_dir):
            ruta_archivo = os.path.join(log_dir, archivo)
            
            # Solo procesar archivos rotados (con número en el nombre)
            if os.path.isfile(ruta_archivo) and '.log.' in archivo:
                try:
                    # Obtener la fecha de modificación
                    modificacion = datetime.datetime.fromtimestamp(
                        os.path.getmtime(ruta_archivo)
                    ).date()
                    
                    if modificacion < cutoff_date:
                        os.remove(ruta_archivo)
                        archivos_eliminados += 1
                        logger.debug(f"Eliminado archivo de log antiguo: {archivo}")
                    else:
                        archivos_rotados.append(archivo)
                except Exception as e:
                    logger.error(f"Error al procesar archivo de log {archivo}: {str(e)}")
        
        logger.info(f"Limpieza finalizada: {archivos_eliminados} archivos eliminados, {len(archivos_rotados)} archivos rotados mantenidos")
        
    except Exception as e:
        logger.error(f"Error en limpieza de logs antiguos: {str(e)}", exc_info=True)
        
    return True

@log_timezone_operation(logger)
def detectar_problemas_timezone():
    """
    Detecta y reporta posibles problemas de zona horaria en la base de datos.
    Esta función debería ejecutarse periódicamente para detectar problemas
    antes de que causen errores en producción.
    """
    from api.models import Partido
    from django.db.models import Q
    
    logger.info("Iniciando detección de problemas de zona horaria")
    
    try:
        # Buscar partidos con fechas en el futuro cercano
        today = get_today_date()
        today_dt = date_to_datetime(today)
        next_week = today + datetime.timedelta(days=7)
        next_week_dt = date_to_datetime(next_week, datetime.time.max)
        
        logger.debug(f"Analizando partidos entre {today_dt} y {next_week_dt}")
        
        # Detectar partidos sin zona horaria correcta
        partidos = Partido.objects.filter(
            Q(fecha__gte=today_dt) & Q(fecha__lte=next_week_dt)
        ).select_related('equipo_1', 'equipo_2')
        
        problemas_detectados = 0
        
        for partido in partidos:
            # Verificar si la fecha tiene zona horaria
            if detect_naive_datetime(partido.fecha, logger):
                problemas_detectados += 1
                logger.warning(
                    f"Partido con fecha sin zona horaria detectado: "
                    f"ID={partido.id}, {partido.equipo_1.nombre} vs {partido.equipo_2.nombre}, "
                    f"Fecha={partido.fecha}"
                )
        
        if problemas_detectados == 0:
            logger.info("No se detectaron problemas de zona horaria en los próximos partidos")
        else:
            logger.warning(
                f"Se detectaron {problemas_detectados} partidos con problemas de zona horaria. "
                f"Revisar timezone.log para más detalles."
            )
    
    except Exception as e:
        logger.error(f"Error en detección de problemas de zona horaria: {str(e)}", exc_info=True)
    
    return True

if __name__ == "__main__":
    # Permitir ejecutar este script directamente desde línea de comandos
    import django
    import sys
    
    # Configurar Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'goolstar_backend.settings')
    django.setup()
    
    # Determinar qué función ejecutar
    if len(sys.argv) > 1:
        tarea = sys.argv[1]
        
        if tarea == "estadisticas":
            actualizar_estadisticas_diarias()
        elif tarea == "limpiar_logs":
            dias = int(sys.argv[2]) if len(sys.argv) > 2 else 30
            limpiar_logs_antiguos(dias)
        elif tarea == "check_timezone":
            detectar_problemas_timezone()
        else:
            print(f"Tarea desconocida: {tarea}")
            print("Tareas disponibles: estadisticas, limpiar_logs, check_timezone")
    else:
        print("Uso: python scheduled_tasks.py [tarea] [parámetros]")
        print("Tareas disponibles: estadisticas, limpiar_logs, check_timezone")
