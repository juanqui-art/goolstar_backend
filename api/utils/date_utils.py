"""
Utilidades para el manejo consistente de fechas y zonas horarias en GoolStar.

Este módulo resuelve problemas comunes relacionados con fechas y zonas horarias:
- Conversión segura entre objetos date y datetime
- Operaciones con fechas que preservan zonas horarias
- Funciones auxiliares para trabajar con rangos de fechas
"""

from datetime import datetime, date, time, timedelta
from django.utils import timezone


def get_today_date():
    """
    Devuelve la fecha actual como objeto date.
    Reemplaza el uso de timezone.now().date()
    """
    return timezone.localdate()


def date_to_datetime(fecha_date, hora=None):
    """
    Convierte un objeto date en un objeto datetime con zona horaria.
    
    Args:
        fecha_date: Objeto date a convertir
        hora: Objeto time opcional. Si no se proporciona, se usa medianoche.
    
    Returns:
        Un objeto datetime aware (con zona horaria)
    """
    if hora is None:
        hora = time.min  # medianoche
    
    naive_datetime = datetime.combine(fecha_date, hora)
    return timezone.make_aware(naive_datetime)


def today_start_datetime():
    """
    Devuelve un objeto datetime aware para el inicio del día actual.
    """
    return date_to_datetime(timezone.localdate())


def today_end_datetime():
    """
    Devuelve un objeto datetime aware para el final del día actual.
    """
    return date_to_datetime(timezone.localdate(), time.max)


def get_date_range(start_date, days):
    """
    Genera un rango de fechas desde start_date hasta start_date + days.
    
    Args:
        start_date: Fecha inicial (date u objeto datetime con timezone)
        days: Número de días a incluir
    
    Returns:
        Tuple con (datetime_inicio, datetime_fin) ambos con zona horaria
    """
    # Convertir a date si es datetime
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    
    # Asegurar que tenemos objetos datetime con zona horaria
    inicio = date_to_datetime(start_date)
    fin = date_to_datetime(start_date + timedelta(days=days), time.max)
    
    return inicio, fin
