# Utilidades de GoolStar

## Manejo de Zonas Horarias (date_utils.py)

### Problema Resuelto

En Django con `USE_TZ = True`, todos los objetos datetime deben incluir información de zona horaria ('aware'). 
Sin embargo, muchas operaciones comunes en Python producen fechas sin zona horaria ('naive'), generando advertencias 
como "DateTimeField received a naive datetime while time zone support is active".

Específicamente se detectaron problemas en:
1. Uso directo de `timezone.now().date()` cuando se filtraba por fechas
2. Combinación de objetos `date` con `timedelta` sin considerar zona horaria
3. Falta de estandarización en la manipulación de fechas

### Soluciones Implementadas

Se creó el módulo `date_utils.py` que proporciona funciones para:

- **Obtener fechas actuales**: `get_today_date()` - Alternativa segura a `timezone.now().date()`
- **Conversión entre tipos**: `date_to_datetime()` - Convierte objetos `date` a `datetime` con zona horaria
- **Rangos de fechas**: `get_date_range()` - Genera rangos de fechas con manejo adecuado de zona horaria
- **Inicio/fin de día**: `today_start_datetime()` y `today_end_datetime()` - Para consultas que necesitan rango completo del día

### Cómo Usar

```python
from api.utils.date_utils import get_today_date, date_to_datetime

# En lugar de esto:
fecha_actual = timezone.now().date()  # ❌ Pierde información de zona horaria

# Usar esto:
fecha_actual_date = get_today_date()  # ✅ Objeto date seguro
fecha_actual_datetime = date_to_datetime(fecha_actual_date)  # ✅ Datetime con timezone

# Para filtros en consultas:
Modelo.objects.filter(
    fecha_campo__gte=date_to_datetime(fecha_inicio),
    fecha_campo__lte=date_to_datetime(fecha_fin, time.max)
)
```

### Mejores Prácticas

1. **Siempre usar `timezone.now()`** en lugar de `datetime.now()` cuando se necesite el tiempo actual
2. **Guardar resultados de `.date()`** en variables separadas cuando sea necesario
3. **Usar `date_to_datetime()`** para convertir objetos `date` a `datetime` con zona horaria
4. **Separar claramente** la lógica de fecha de la lógica de hora

### Archivos Actualizados

1. **api/utils/date_utils.py**: Nuevo módulo con utilidades de fecha
2. **api/views.py**: Actualizado `PartidoViewSet.proximos()` para usar las nuevas utilidades
3. **api/tests/test_api_nuevos_endpoints.py**: Actualizado método `make_aware_date()` en las clases de test
