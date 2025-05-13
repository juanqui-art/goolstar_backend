from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
import logging

# Configurar logger
logger = logging.getLogger(__name__)

# Importar los modelos necesarios
from .models.competicion import Partido


@receiver(post_save, sender=Partido)
def actualizar_estadisticas_partido(sender, instance, created, **kwargs):
    """
    Señal que se ejecuta después de guardar un objeto Partido.
    Si el partido acaba de ser marcado como completado, actualiza las estadísticas
    relacionadas con el partido.
    """
    # Verificar si el partido fue marcado como completado
    # El atributo _actualizar_estadisticas es establecido en el método save() del modelo
    if hasattr(instance, '_actualizar_estadisticas') and instance._actualizar_estadisticas:
        try:
            logger.info(f"Actualizando estadísticas para el partido {instance.id} entre {instance.equipo_1} y {instance.equipo_2}")
            # Llamar al método para actualizar estadísticas
            instance.actualizar_estadisticas_post_save()
            # Eliminar el atributo para evitar actualizaciones innecesarias
            delattr(instance, '_actualizar_estadisticas')
            logger.info(f"Estadísticas actualizadas correctamente para el partido {instance.id}")
        except Exception as e:
            # Capturar cualquier error para que no interrumpa el flujo normal de la aplicación
            logger.error(f"Error al actualizar estadísticas para el partido {instance.id}: {str(e)}")
            # No propagamos la excepción para evitar que falle el guardado del partido


@receiver(pre_delete, sender=Partido)
def limpiar_estadisticas_partido(sender, instance, **kwargs):
    """
    Señal que se ejecuta antes de eliminar un Partido.
    Si el partido estaba completado, actualiza las estadísticas relacionadas
    para reflejar que el partido ya no existe.
    """
    if instance.completado:
        try:
            logger.info(f"Limpiando estadísticas antes de eliminar el partido {instance.id}")
            # Obtener las estadísticas de ambos equipos
            from .models.estadisticas import EstadisticaEquipo
            from django.db import transaction
            
            # Usar transacción atómica para asegurar consistencia
            with transaction.atomic():
                # Temporalmente marcar el partido como no completado para que no se incluya en actualizar_estadisticas
                instance.completado = False
                # No guardamos el cambio en la base de datos, solo afectamos el objeto en memoria
                
                for equipo in [instance.equipo_1, instance.equipo_2]:
                    estadistica = EstadisticaEquipo.objects.filter(
                        equipo=equipo,
                        torneo=instance.torneo
                    ).first()
                    
                    if estadistica:
                        # Actualizar las estadísticas sin incluir este partido
                        estadistica.actualizar_estadisticas()
                        logger.info(f"Estadísticas actualizadas para el equipo {equipo.id} antes de eliminar el partido")
                
                # Restaurar el estado para no afectar otras operaciones
                instance.completado = True
        except Exception as e:
            logger.error(f"Error al limpiar estadísticas antes de eliminar el partido {instance.id}: {str(e)}")
            # No propagamos la excepción para permitir que el partido se elimine