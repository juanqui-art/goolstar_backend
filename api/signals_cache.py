"""
Signals para invalidar cache automáticamente cuando se modifican modelos.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from api.models import Partido, Gol, Tarjeta, Equipo, Torneo
from api.models.estadisticas import EstadisticaEquipo
from api.utils.cache_utils import invalidate_partido_cache, invalidate_equipo_cache, invalidate_torneo_cache
from api.utils.logging_utils import get_logger

logger = get_logger(__name__)


@receiver([post_save, post_delete], sender=Partido)
def invalidate_partido_related_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica un partido"""
    try:
        invalidated = invalidate_partido_cache(instance.id)
        logger.info(f"Cache invalidado para partido {instance.id}: {invalidated} claves eliminadas")
        
        # También invalidar cache del torneo relacionado
        if instance.torneo:
            torneo_invalidated = invalidate_torneo_cache(instance.torneo.id)
            logger.info(f"Cache invalidado para torneo {instance.torneo.id}: {torneo_invalidated} claves eliminadas")
            
    except Exception as e:
        logger.error(f"Error invalidando cache para partido {instance.id}: {str(e)}")


@receiver([post_save, post_delete], sender=Gol)
def invalidate_gol_related_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica un gol"""
    try:
        # Invalidar cache del partido relacionado
        if instance.partido:
            invalidated = invalidate_partido_cache(instance.partido.id)
            logger.info(f"Cache invalidado por gol en partido {instance.partido.id}: {invalidated} claves eliminadas")
            
            # También invalidar estadísticas y tabla de posiciones
            if instance.partido.torneo:
                torneo_invalidated = invalidate_torneo_cache(instance.partido.torneo.id)
                logger.info(f"Cache invalidado para torneo {instance.partido.torneo.id}: {torneo_invalidated} claves eliminadas")
                
    except Exception as e:
        logger.error(f"Error invalidando cache para gol {instance.id}: {str(e)}")


@receiver([post_save, post_delete], sender=Tarjeta)
def invalidate_tarjeta_related_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica una tarjeta"""
    try:
        # Invalidar cache del partido relacionado
        if instance.partido:
            invalidated = invalidate_partido_cache(instance.partido.id)
            logger.info(f"Cache invalidado por tarjeta en partido {instance.partido.id}: {invalidated} claves eliminadas")
            
            # También invalidar estadísticas
            if instance.partido.torneo:
                torneo_invalidated = invalidate_torneo_cache(instance.partido.torneo.id)
                logger.info(f"Cache invalidado para torneo {instance.partido.torneo.id}: {torneo_invalidated} claves eliminadas")
                
    except Exception as e:
        logger.error(f"Error invalidando cache para tarjeta {instance.id}: {str(e)}")


@receiver([post_save, post_delete], sender=Equipo)
def invalidate_equipo_related_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica un equipo"""
    try:
        invalidated = invalidate_equipo_cache(instance.id)
        logger.info(f"Cache invalidado para equipo {instance.id}: {invalidated} claves eliminadas")
        
        # También invalidar cache de la categoría
        if instance.categoria:
            from api.utils.cache_utils import CacheManager
            categoria_invalidated = CacheManager.invalidate_pattern(f"equipos_categoria*{instance.categoria.id}*")
            logger.info(f"Cache invalidado para categoría {instance.categoria.id}: {categoria_invalidated} claves eliminadas")
            
    except Exception as e:
        logger.error(f"Error invalidando cache para equipo {instance.id}: {str(e)}")


@receiver([post_save, post_delete], sender=EstadisticaEquipo)
def invalidate_estadisticas_cache(sender, instance, **kwargs):
    """Invalidar cache cuando se modifican estadísticas"""
    try:
        # Invalidar tabla de posiciones y estadísticas del torneo
        if instance.torneo:
            invalidated = invalidate_torneo_cache(instance.torneo.id)
            logger.info(f"Cache invalidado por estadísticas en torneo {instance.torneo.id}: {invalidated} claves eliminadas")
            
    except Exception as e:
        logger.error(f"Error invalidando cache para estadística {instance.id}: {str(e)}")


@receiver([post_save, post_delete], sender=Torneo)
def invalidate_torneo_cache_signal(sender, instance, **kwargs):
    """Invalidar cache cuando se modifica un torneo"""
    try:
        invalidated = invalidate_torneo_cache(instance.id)
        logger.info(f"Cache invalidado para torneo {instance.id}: {invalidated} claves eliminadas")
        
    except Exception as e:
        logger.error(f"Error invalidando cache para torneo {instance.id}: {str(e)}")