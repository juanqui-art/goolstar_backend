"""
Utilidades para manejo de cache con Redis.
"""
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Any, Optional, Callable


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Genera una clave de cache única basada en los parámetros.
    
    Args:
        prefix: Prefijo para la clave
        *args: Argumentos adicionales
        **kwargs: Argumentos con nombre
    
    Returns:
        str: Clave de cache única
    """
    # Crear string único con todos los parámetros
    params = {
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    
    params_str = json.dumps(params, sort_keys=True, default=str)
    params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
    
    return f"{prefix}_{params_hash}"


def cached_view_result(cache_key_prefix: str, timeout: Optional[int] = None):
    """
    Decorador para cachear resultados de vistas/métodos.
    
    Args:
        cache_key_prefix: Prefijo para la clave de cache
        timeout: Tiempo de vida del cache en segundos
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única
            cache_key = generate_cache_key(cache_key_prefix, *args, **kwargs)
            
            # Intentar obtener del cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Si no está en cache, ejecutar función
            result = func(*args, **kwargs)
            
            # Determinar timeout
            ttl = timeout or getattr(settings, 'CACHE_TTL', {}).get(cache_key_prefix, 300)
            
            # Guardar en cache
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


class CacheManager:
    """Manejador de cache para operaciones comunes"""
    
    @staticmethod
    def get_or_set_queryset(cache_key: str, queryset_func: Callable, timeout: int = 300) -> Any:
        """
        Obtiene datos del cache o ejecuta queryset y los guarda.
        
        Args:
            cache_key: Clave única para el cache
            queryset_func: Función que retorna el queryset/datos
            timeout: Tiempo de vida en segundos
        
        Returns:
            Datos del cache o del queryset
        """
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Ejecutar queryset y convertir a lista para serializar
        data = list(queryset_func())
        cache.set(cache_key, data, timeout)
        
        return data
    
    @staticmethod
    def invalidate_pattern(pattern: str) -> int:
        """
        Invalida todas las claves que coincidan con un patrón.
        
        Args:
            pattern: Patrón de búsqueda (ej: "equipos_*")
        
        Returns:
            int: Número de claves eliminadas
        """
        try:
            # Verificar si estamos usando Redis
            cache_backend = settings.CACHES['default']['BACKEND']
            
            if 'redis' in cache_backend.lower():
                from django_redis import get_redis_connection
                redis_conn = get_redis_connection("default")
                
                # Buscar claves que coincidan con el patrón
                key_prefix = settings.CACHES['default'].get('KEY_PREFIX', '')
                full_pattern = f"{key_prefix}:*{pattern}*" if key_prefix else f"*{pattern}*"
                keys = redis_conn.keys(full_pattern)
                
                if keys:
                    return redis_conn.delete(*keys)
                return 0
            else:
                # Para cache en memoria local, solo limpiar todo el cache
                # ya que no podemos hacer búsqueda por patrón
                cache.clear()
                return 1  # Retornar 1 para indicar que se hizo limpieza
        except Exception:
            # Si hay cualquier error, no hacer nada
            return 0
    
    @staticmethod
    def clear_cache_for_model(model_name: str) -> int:
        """
        Limpia cache relacionado con un modelo específico.
        
        Args:
            model_name: Nombre del modelo (ej: "equipo", "partido")
        
        Returns:
            int: Número de claves eliminadas
        """
        patterns_to_clear = [
            f"{model_name}_*",
            f"*_{model_name}_*",
            f"tabla_posiciones*" if model_name in ['partido', 'gol'] else "",
            f"estadisticas*" if model_name in ['partido', 'gol', 'tarjeta'] else ""
        ]
        
        total_deleted = 0
        for pattern in patterns_to_clear:
            if pattern:  # Solo si el patrón no está vacío
                total_deleted += CacheManager.invalidate_pattern(pattern)
        
        return total_deleted


# Funciones de conveniencia para modelos específicos
def invalidate_equipo_cache(equipo_id: Optional[int] = None) -> int:
    """Invalida cache relacionado con equipos"""
    patterns = ["equipos_", "tabla_posiciones", "estadisticas_equipo"]
    if equipo_id:
        patterns.append(f"equipo_{equipo_id}")
    
    total = 0
    for pattern in patterns:
        total += CacheManager.invalidate_pattern(pattern)
    return total


def invalidate_partido_cache(partido_id: Optional[int] = None) -> int:
    """Invalida cache relacionado con partidos"""
    patterns = ["partidos_", "tabla_posiciones", "estadisticas", "proximos"]
    if partido_id:
        patterns.append(f"partido_{partido_id}")
    
    total = 0
    for pattern in patterns:
        total += CacheManager.invalidate_pattern(pattern)
    return total


def invalidate_torneo_cache(torneo_id: Optional[int] = None) -> int:
    """Invalida cache relacionado con torneos"""
    patterns = ["torneo_", "tabla_posiciones", "estadisticas"]
    if torneo_id:
        patterns.append(f"torneo_{torneo_id}")
    
    total = 0
    for pattern in patterns:
        total += CacheManager.invalidate_pattern(pattern)
    return total