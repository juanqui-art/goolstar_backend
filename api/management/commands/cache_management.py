"""
Comando para gestionar cache de Redis.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from api.utils.cache_utils import CacheManager
import json


class Command(BaseCommand):
    help = 'Gestionar cache de Redis - ver estadísticas, limpiar, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['stats', 'clear', 'clear-pattern', 'test'],
            required=True,
            help='Acción a realizar con el cache'
        )
        parser.add_argument(
            '--pattern',
            type=str,
            help='Patrón para limpiar cache específico (solo con clear-pattern)'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'stats':
            self.show_cache_stats()
        elif action == 'clear':
            self.clear_all_cache()
        elif action == 'clear-pattern':
            pattern = options.get('pattern')
            if not pattern:
                self.stdout.write(
                    self.style.ERROR('Debes especificar --pattern con clear-pattern')
                )
                return
            self.clear_cache_pattern(pattern)
        elif action == 'test':
            self.test_cache()

    def show_cache_stats(self):
        """Mostrar estadísticas del cache"""
        self.stdout.write(self.style.SUCCESS('📊 ESTADÍSTICAS DEL CACHE'))
        self.stdout.write('=' * 50)
        
        # Mostrar tipo de cache configurado
        cache_backend = settings.CACHES['default']['BACKEND']
        self.stdout.write(f"🔧 Backend: {cache_backend}")
        
        if 'redis' in cache_backend.lower():
            try:
                from django_redis import get_redis_connection
                redis_conn = get_redis_connection("default")
                
                # Información básica
                info = redis_conn.info()
                self.stdout.write(f"🔧 Versión Redis: {info.get('redis_version', 'N/A')}")
                self.stdout.write(f"💾 Memoria usada: {info.get('used_memory_human', 'N/A')}")
                self.stdout.write(f"🔑 Total de claves: {info.get('db0', {}).get('keys', 0)}")
                
                # Buscar claves por prefijo
                prefix = settings.CACHES['default'].get('KEY_PREFIX', '')
                if prefix:
                    pattern = f"{prefix}:*"
                    keys = redis_conn.keys(pattern)
                    
                    self.stdout.write(f"\n📋 CLAVES DE GOOLSTAR ({len(keys)} total):")
                    
                    # Agrupar por tipo
                    cache_types = {}
                    for key in keys:
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        # Extraer tipo del prefijo
                        parts = key_str.split(':')
                        if len(parts) >= 2:
                            cache_type = parts[1].split('_')[0]
                            cache_types[cache_type] = cache_types.get(cache_type, 0) + 1
                    
                    for cache_type, count in sorted(cache_types.items()):
                        self.stdout.write(f"  • {cache_type}: {count} claves")
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error obteniendo estadísticas de Redis: {str(e)}')
                )
        else:
            self.stdout.write("ℹ️ Usando cache en memoria local (LocMemCache)")
            self.stdout.write("   • No se pueden mostrar estadísticas detalladas")
            self.stdout.write("   • Cache se reinicia al reiniciar el servidor")

    def clear_all_cache(self):
        """Limpiar todo el cache"""
        self.stdout.write('🧹 Limpiando todo el cache...')
        
        try:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('✅ Cache limpiado exitosamente')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error limpiando cache: {str(e)}')
            )

    def clear_cache_pattern(self, pattern):
        """Limpiar cache que coincida con un patrón"""
        self.stdout.write(f'🧹 Limpiando cache con patrón: {pattern}')
        
        try:
            deleted = CacheManager.invalidate_pattern(pattern)
            self.stdout.write(
                self.style.SUCCESS(f'✅ {deleted} claves eliminadas')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error limpiando cache: {str(e)}')
            )

    def test_cache(self):
        """Probar funcionamiento del cache"""
        self.stdout.write('🧪 PROBANDO CACHE')
        self.stdout.write('=' * 30)
        
        # Prueba básica
        test_key = 'test_cache_key'
        test_value = {'mensaje': 'Hola desde cache', 'timestamp': 123456}
        
        try:
            # Escribir al cache
            cache.set(test_key, test_value, 60)
            self.stdout.write('✅ Escritura al cache: OK')
            
            # Leer del cache
            cached_value = cache.get(test_key)
            if cached_value == test_value:
                self.stdout.write('✅ Lectura del cache: OK')
            else:
                self.stdout.write('❌ Lectura del cache: FALLO')
                return
            
            # Eliminar del cache
            cache.delete(test_key)
            cached_value = cache.get(test_key)
            if cached_value is None:
                self.stdout.write('✅ Eliminación del cache: OK')
            else:
                self.stdout.write('❌ Eliminación del cache: FALLO')
                return
                
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Todas las pruebas de cache pasaron!')
            )
            
            # Mostrar configuración
            self.stdout.write('\n⚙️ CONFIGURACIÓN:')
            redis_url = getattr(settings, 'CACHES', {}).get('default', {}).get('LOCATION', 'N/A')
            self.stdout.write(f"  Redis URL: {redis_url}")
            
            cache_ttl = getattr(settings, 'CACHE_TTL', {})
            self.stdout.write(f"  TTL configurados: {json.dumps(cache_ttl, indent=2)}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error en pruebas de cache: {str(e)}')
            )