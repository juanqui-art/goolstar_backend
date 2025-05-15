# Guía de Logging para GoolStar

Este documento explica cómo está configurado el sistema de logging en GoolStar y cómo usarlo correctamente
en diferentes partes de la aplicación.

## Configuración General

El sistema de logging de GoolStar está configurado para:

1. Registrar eventos en diferentes niveles (DEBUG, INFO, WARNING, ERROR, CRITICAL)
2. Almacenar logs en archivos separados por nivel de severidad (debug.log, info.log, error.log)
3. Rotar archivos de log cuando alcanzan 10MB (con un máximo de 10 copias de respaldo)
4. Enviar notificaciones por email a los administradores cuando ocurren errores en producción
5. Mostrar logs detallados en la consola durante el desarrollo
6. Registrar específicamente problemas relacionados con zonas horarias en timezone.log
7. Capturar todas las solicitudes HTTP mediante un middleware especializado

## Niveles de Logging

| Nivel | Uso recomendado | Ejemplo |
|-------|----------------|---------|
| DEBUG | Información detallada para depuración | "Procesando registro ID=123" |
| INFO | Confirmación de operaciones normales | "Usuario autenticado correctamente" |
| WARNING | Situaciones inesperadas pero no críticas | "Formato de fecha inválido, usando valor por defecto" |
| ERROR | Errores que impiden una operación específica | "No se pudo guardar el partido por datos inválidos" |
| CRITICAL | Errores graves que pueden afectar toda la app | "Conexión a base de datos perdida" |

## Cómo utilizar el logging en el código

### 1. Importar y configurar el logger

Ejemplo:

```python
from api.utils.logging_utils import get_logger

# Usar __name__ para identificar automáticamente el módulo actual
logger = get_logger(__name__)
```

### 2. Registrar eventos en diferentes niveles

Ejemplos:

```python
# Información de depuración (desarrollo)
logger.debug("Procesando partido {} con opciones: {}".format(partido_id, opciones))

# Operaciones normales
logger.info("Partido {} guardado correctamente".format(partido_id))

# Advertencias
logger.warning("Fecha {} posiblemente incorrecta".format(fecha))

# Errores
logger.error("Error al procesar partido {}: {}".format(partido_id, str(e)))

# Errores críticos (con stack trace completo)
logger.critical("Fallo en la conexión a la base de datos", exc_info=True)
```

### 3. Utilizar decoradores para logging automático

GoolStar incluye decoradores especiales para funcionalidades comunes:

#### Decorador para vistas y endpoints de API

Ejemplo:

```python
from api.utils.logging_utils import get_logger, log_api_request

logger = get_logger(__name__)

@log_api_request(logger)
def mi_vista(request):
    # Tu código aquí
    return Response(...)
```

Este decorador registra automáticamente:
- La solicitud entrante (método, ruta, dirección IP)
- Parámetros (si DEBUG está activado)
- Tiempo de respuesta
- Cualquier excepción no manejada

#### Decorador para operaciones de base de datos

Ejemplo:

```python
from api.utils.logging_utils import log_db_operation

@log_db_operation(logger)
def actualizar_estadisticas(equipo_id):
    # Operaciones de base de datos
    pass
```

#### Decorador para operaciones con zonas horarias

Ejemplo:

```python
from api.utils.tz_logging import log_timezone_operation

@log_timezone_operation(logger)
def procesar_fechas_partidos(fecha_inicio, fecha_fin):
    # Operaciones con fechas y zonas horarias
    pass
```

### 4. Detección de problemas con zonas horarias

GoolStar incluye utilidades específicas para detectar y registrar problemas relacionados con zonas horarias:

```python
from api.utils.tz_logging import detect_naive_datetime, log_date_conversion

# Detectar fechas sin zona horaria
if detect_naive_datetime(fecha, logger):
    # Manejar el problema

# Registrar conversiones de fecha
log_date_conversion(fecha_original, fecha_convertida, logger)
```

## Archivos de Log

Los archivos de log se almacenan en el directorio `/logs/` y son:

- `debug.log` - Todos los mensajes (nivel DEBUG y superior)
- `info.log` - Mensajes informativos y superiores (INFO, WARNING, ERROR, CRITICAL)
- `error.log` - Solo mensajes de error (ERROR, CRITICAL)
- `timezone.log` - Específico para problemas de zona horaria

## Middleware de Logging HTTP

GoolStar incluye un middleware que registra automáticamente todas las solicitudes HTTP:

- Solicitudes entrantes (método, ruta, usuario, dirección IP)
- Respuestas salientes (código de estado, tiempo de respuesta)
- Detalles adicionales para errores (códigos 4xx y 5xx)

Este middleware está configurado automáticamente en settings.py y no requiere configuración adicional.

## Notificaciones por Email

En producción, los errores se envían automáticamente por email a los administradores configurados en la variable `ADMINS` del archivo `.env`.

## Herramientas de Análisis de Logs

GoolStar incluye herramientas para analizar los logs y detectar patrones de errores:

### Log Analyzer

La clase `LogAnalyzer` en `api/utils/log_analyzer.py` permite:

- Analizar archivos de log para detectar patrones
- Generar reportes de errores
- Detectar específicamente problemas de zona horaria
- Generar estadísticas sobre la frecuencia de errores

Ejemplo de uso:

```python
from api.utils.log_analyzer import LogAnalyzer

# Analizar logs de los últimos 7 días
analyzer = LogAnalyzer()
report = analyzer.generate_report(days_back=7)

# Buscar específicamente problemas de zonas horarias
naive_datetimes = analyzer.detect_naive_datetimes()
```

También puede usarse desde la línea de comandos:

```bash
python -m api.utils.log_analyzer --days=7 --output=reporte.json
```

## Tareas Programadas con Logging

Para las tareas programadas, GoolStar proporciona utilidades en `api/utils/scheduled_tasks.py` que incluyen:

- Actualización de estadísticas con logging integrado
- Limpieza de logs antiguos
- Detección de problemas de zona horaria

Ejemplo de uso:

```bash
python -m api.utils.scheduled_tasks estadisticas
python -m api.utils.scheduled_tasks limpiar_logs 30
python -m api.utils.scheduled_tasks check_timezone
```

## Mejores prácticas

1. **Sea descriptivo pero conciso**: Los mensajes deben ser claros pero no excesivamente largos
2. **Incluya información contextual**: IDs, nombres de usuario, parámetros importantes
3. **Evite información sensible**: No registre contraseñas, tokens o datos personales sensibles
4. **Use el nivel adecuado**: No use ERROR para situaciones normales o esperadas
5. **Agregue stack traces cuando sea útil**: Use `exc_info=True` para errores importantes
6. **Contextualice excepciones**: En lugar de solo registrar `str(e)`, añada contexto sobre lo que estaba haciendo
7. **Utilice los decoradores de logging**: Aproveche `log_api_request`, `log_db_operation` y `log_timezone_operation`
8. **Preste especial atención a las fechas**: Use siempre las utilidades de `date_utils.py` y registre problemas con `tz_logging.py`

## Ejemplo completo

A continuación se muestra un ejemplo de uso completo del sistema de logging en un ViewSet:

```python
# Importaciones necesarias
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.response import Response
from api.utils.logging_utils import get_logger, log_api_request
from api.utils.date_utils import get_today_date, date_to_datetime
from api.utils.tz_logging import detect_naive_datetime

# Configurar el logger para el módulo actual
logger = get_logger(__name__)

class MiViewSet(viewsets.ModelViewSet):
    """Un ViewSet de ejemplo con logging integrado"""
    
    @log_api_request(logger)
    def create(self, request, *args, **kwargs):
        """Ejemplo de método create con logging detallado"""
        logger.info("Iniciando creación de recurso - Usuario: {}".format(request.user))
        
        try:
            # Lógica principal
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Verificar fechas
            fecha = serializer.validated_data.get('fecha')
            if fecha and detect_naive_datetime(fecha, logger):
                # Corregir fecha
                fecha = date_to_datetime(fecha.date())
                serializer.validated_data['fecha'] = fecha
                logger.warning("Se corrigió una fecha sin zona horaria")
            
            self.perform_create(serializer)
            resultado = serializer.instance
            
            logger.info("Recurso creado exitosamente - ID: {}".format(resultado.id))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            # Error de validación (cliente)
            logger.warning(
                "Datos inválidos enviados por el usuario {}: {}".format(
                    request.user, str(e)
                )
            )
            return Response(
                {"error": "Los datos proporcionados no son válidos", "detalles": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Error inesperado (servidor)
            logger.error(
                "Error inesperado al crear recurso por usuario {}: {}".format(
                    request.user, str(e)
                ),
                exc_info=True
            )
            return Response(
                {"error": "Se produjo un error inesperado al procesar la solicitud"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
