from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """
        Método ejecutado cuando la aplicación está lista.
        Importamos las señales para asegurar que sean registradas.
        """
        import api.signals  # importamos las señales para registrarlas
        import api.signals_cache  # importamos las señales de cache
