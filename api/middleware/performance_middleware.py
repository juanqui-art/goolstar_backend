"""
Middleware para medir performance de queries y tiempo de respuesta.
Solo se activa en desarrollo para evitar overhead en producción.
"""
import time

from django.conf import settings
from django.db import connection


class PerformanceMiddleware:
    """Middleware para medir queries y tiempo de respuesta en desarrollo"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Solo medir en desarrollo
        if not settings.DEBUG:
            return self.get_response(request)

        # Resetear contador de queries
        queries_before = len(connection.queries)
        start_time = time.time()

        # Procesar request
        response = self.get_response(request)

        # Calcular métricas
        end_time = time.time()
        queries_after = len(connection.queries)

        # Métricas calculadas
        total_time = round((end_time - start_time) * 1000, 2)  # en ms
        query_count = queries_after - queries_before

        # Agregar headers de performance
        response['X-Query-Count'] = str(query_count)
        response['X-Response-Time'] = f"{total_time}ms"

        # Log para endpoints API críticos
        if request.path.startswith('/api/') and query_count > 10:
            print(f"⚠️  HIGH QUERY COUNT: {request.path}")
            print(f"   Queries: {query_count} | Time: {total_time}ms")

        return response
