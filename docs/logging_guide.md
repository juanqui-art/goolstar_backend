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

[//]: # (```python)
[//]: # (from api.utils.logging_utils import get_logger)
[//]: # ()
[//]: # (# Usar __name__ para identificar automáticamente el módulo actual)
[//]: # (logger = get_logger(__name__))
[//]: # (```)

### 2. Registrar eventos en diferentes niveles

Ejemplos:

```python
# Información de depuración (desarrollo)
# logger.debug("Procesando partido {} con opciones: {}".format(partido_id, opciones))

# Operaciones normales
# logger.info("Partido {} guardado correctamente".format(partido_id))

# Advertencias
# logger.warning("Fecha {} posiblemente incorrecta".format(fecha))

# Errores
# logger.error("Error al procesar partido {}: {}".format(partido_id, str(e)))

# Errores críticos (con stack trace completo)

# (logger.critical&#40;"Fallo en la conexión a la base de datos", exc_info=True&#41;)
```

### 3. Utilizar decoradores para logging automático

GoolStar incluye decoradores especiales para funcionalidades comunes:

#### Decorador para vistas y endpoints de API

Ejemplo:

```python
# from api.utils.logging_utils import log_api_request

# @log_api_request(logger)
# def mi_vista(request):
#     # Tu código aquí
#     return Response(...)

```

Este decorador registra automáticamente:
- La solicitud entrante (método, ruta, dirección IP)
- Parámetros (si DEBUG está activado)
- Tiempo de respuesta
- Cualquier excepción no manejada

#### Decorador para operaciones de base de datos

Ejemplo:

```python
# from api.utils.logging_utils import log_db_operation

# @log_db_operation(logger)
# def actualizar_estadisticas(equipo_id):
#     # Operaciones de base de datos
#     pass

```

## Archivos de Log

Los archivos de log se almacenan en el directorio `/logs/` y son:

- `debug.log` - Todos los mensajes (nivel DEBUG y superior)
- `info.log` - Mensajes informativos y superiores (INFO, WARNING, ERROR, CRITICAL)
- `error.log` - Solo mensajes de error (ERROR, CRITICAL)

## Notificaciones por Email

En producción, los errores se envían automáticamente por email a los administradores configurados en la variable `ADMINS` del archivo `.env`.

## Mejores prácticas

1. **Sea descriptivo pero conciso**: Los mensajes deben ser claros pero no excesivamente largos
2. **Incluya información contextual**: IDs, nombres de usuario, parámetros importantes
3. **Evite información sensible**: No registre contraseñas, tokens o datos personales sensibles
4. **Use el nivel adecuado**: No use ERROR para situaciones normales o esperadas
5. **Agregue stack traces cuando sea útil**: Use `exc_info=True` para errores importantes
6. **Contextualice excepciones**: En lugar de solo registrar `str(e)`, añada contexto sobre lo que estaba haciendo

## Ejemplo completo

A continuación se muestra un ejemplo de uso completo del sistema de logging en un ViewSet:

```python
# Importaciones necesarias
from django.core.exceptions import ValidationError
from rest_framework import viewsets, status
from rest_framework.response import Response
from api.utils.logging_utils import get_logger, log_api_request

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

```
