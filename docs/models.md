# Documentación de Modelos - Sistema GoolStar

## Introducción

El sistema GoolStar es una plataforma de gestión de torneos de fútbol que permite administrar equipos, jugadores, partidos, estadísticas y finanzas. Esta documentación detalla la estructura de los modelos de datos que conforman el sistema.

## Estructura del Proyecto

El sistema utiliza una arquitectura modular para organizar los modelos según su función:

```
api/
└── models/
    ├── __init__.py       # Importa todos los modelos
    ├── base.py           # Modelos base del sistema
    ├── participantes.py  # Modelos de participantes
    ├── competicion.py    # Modelos relacionados con la competición
    ├── estadisticas.py   # Modelos para estadísticas
    ├── financiero.py     # Modelos para gestión financiera
    └── participacion.py  # Modelos para participación en partidos
```

## Modelos Base (`base.py`)

### Nivel
Enumeración que define los niveles de habilidad para jugadores y equipos.

| Valor | Descripción |
|-------|-------------|
| 1 | Muy bajo |
| 2 | Bajo |
| 3 | Medio |
| 4 | Alto |
| 5 | Muy alto |

### Categoria
Define las categorías del torneo (VARONES, DAMAS, MÁSTER) y sus configuraciones.

**Campos principales:**
- `nombre`: Nombre de la categoría
- `descripcion`: Descripción detallada
- `premio_primero`, `premio_segundo`, etc.: Premios para los ganadores
- `costo_inscripcion`: Costo de inscripción para equipos
- `costo_arbitraje`: Costo del arbitraje por partido
- `multa_amarilla`, `multa_roja`: Multas por tarjetas
- `limite_inasistencias`: Número máximo de inasistencias permitidas
- `limite_amarillas_suspension`: Número de tarjetas amarillas para suspensión
- `partidos_suspension_roja`: Partidos de suspensión por tarjeta roja

### Torneo
Configuración y control de torneos.

**Campos principales:**
- `nombre`: Nombre del torneo
- `categoria`: Categoría a la que pertenece
- `fecha_inicio`, `fecha_fin`: Fechas del torneo
- `activo`, `finalizado`: Estado del torneo
- `tiene_fase_grupos`, `tiene_eliminacion_directa`: Formato del torneo
- `numero_grupos`: Cantidad de grupos
- `equipos_clasifican_por_grupo`: Equipos que clasifican por grupo
- `fase_actual`: Estado actual del torneo (inscripción, grupos, eliminatorias, etc.)

**Métodos importantes:**
- `equipos_participantes`: Obtiene equipos activos
- `puede_iniciar_eliminacion`: Verifica si se puede iniciar fase eliminatoria
- `equipos_en_grupo`: Retorna equipos de un grupo específico
- `obtener_clasificados`: Obtiene equipos clasificados de la fase de grupos

### FaseEliminatoria
Fases de eliminación directa del torneo.

**Campos principales:**
- `torneo`: Torneo al que pertenece
- `nombre`: Nombre de la fase (octavos, cuartos, etc.)
- `orden`: Orden de la fase
- `fecha_inicio`, `fecha_fin`: Fechas de la fase
- `completada`: Indica si la fase está completada

**Métodos importantes:**
- `partidos_pendientes`: Cuenta partidos pendientes
- `puede_iniciar_siguiente_fase`: Verifica si se puede iniciar la siguiente fase

## Modelos de Participantes (`participantes.py`)

### Dirigente
Dirigentes de equipos.

**Campos principales:**
- `nombre`: Nombre del dirigente
- `telefono`: Teléfono de contacto

### Equipo
Equipos participantes en el torneo.

**Campos principales:**
- `nombre`: Nombre del equipo
- `categoria`, `torneo`: Categoría y torneo al que pertenece
- `dirigente`: Dirigente del equipo
- `logo`, `color_principal`, `color_secundario`: Identidad visual
- `nivel`: Nivel de habilidad
- `grupo`: Grupo asignado en fase de grupos
- `inasistencias`: Contador de inasistencias
- `excluido_por_inasistencias`: Indica si fue excluido por inasistencias
- `clasificado_fase_grupos`: Indica si clasificó de la fase de grupos
- `fase_actual`, `eliminado_en_fase`: Control de fase eliminatoria

**Métodos importantes:**
- `deuda_total`: Calcula la deuda total del equipo
- `calcular_saldo_total`: Calcula el saldo total del equipo
- `get_total_inscripcion`: Calcula el total de inscripción con multas
- `get_deuda_multas_pendientes`: Calcula deuda por multas pendientes
- `get_tarjetas_no_pagadas`: Obtiene tarjetas no pagadas
- `registrar_abono`: Registra un abono del equipo
- `verificar_suspension_por_inasistencias`: Verifica si debe ser excluido
- `clasificar_a_eliminacion`: Marca el equipo como clasificado
- `eliminar_en_fase`: Marca el equipo como eliminado

### Jugador
Jugadores registrados en cada equipo.

**Campos principales:**
- `primer_nombre`, `segundo_nombre`, `primer_apellido`, `segundo_apellido`: Nombre completo
- `cedula`: Número de identificación
- `fecha_nacimiento`: Fecha de nacimiento
- `equipo`: Equipo al que pertenece
- `numero_dorsal`: Número de camiseta
- `posicion`: Posición en el campo
- `nivel`: Nivel de habilidad
- `foto`: Fotografía del jugador
- `suspendido`: Indica si está suspendido
- `partidos_suspension_restantes`: Partidos que debe cumplir suspendido

**Métodos importantes:**
- `nombre_completo`: Retorna el nombre completo formateado
- `get_amarillas_acumuladas`: Cuenta tarjetas amarillas acumuladas
- `verificar_suspension_por_amarillas`: Verifica si debe ser suspendido
- `puede_jugar`: Verifica si puede participar (no suspendido)

### Arbitro
Árbitros del torneo.

**Campos principales:**
- `nombres`, `apellidos`: Nombre completo
- `telefono`, `email`: Información de contacto
- `activo`: Indica si está activo
- `experiencia_anos`: Años de experiencia
- `categoria_maxima`: Categoría máxima arbitrada

**Métodos importantes:**
- `nombre_completo`: Retorna el nombre completo
- `partidos_arbitrados`: Cuenta partidos arbitrados
- `total_cobrado`: Calcula el total cobrado
- `total_por_cobrar`: Calcula el total por cobrar

## Modelos de Competición (`competicion.py`)

### Jornada
Jornadas del torneo.

**Campos principales:**
- `nombre`: Nombre de la jornada
- `numero`: Número de jornada
- `fecha`: Fecha programada
- `activa`: Indica si está activa

### Partido
Partidos del torneo.

**Campos principales:**
- `torneo`: Torneo al que pertenece
- `jornada`, `fase_eliminatoria`: Jornada o fase a la que pertenece
- `equipo_1`, `equipo_2`: Equipos participantes
- `arbitro`: Árbitro asignado
- `fecha`, `cancha`: Información logística
- `completado`: Indica si está completado
- `goles_equipo_1`, `goles_equipo_2`: Resultado
- `es_eliminatorio`: Indica si es partido eliminatorio
- `penales_equipo_1`, `penales_equipo_2`: Resultado de penales
- `inasistencia_equipo_1`, `inasistencia_equipo_2`: Control de inasistencias
- `equipo_1_pago_arbitro`, `equipo_2_pago_arbitro`: Control de pagos
- `observaciones`: Observaciones del partido
- `acta_firmada`, `acta_firmada_equipo_1`, `acta_firmada_equipo_2`: Control de actas

**Métodos importantes:**
- `get_participaciones_equipo`: Obtiene participaciones de un equipo
- `get_jugadores_titulares`: Obtiene jugadores titulares
- `get_cambios_realizados`: Cuenta cambios realizados
- `validar_minimo_jugadores`: Valida mínimo de jugadores
- `resultado`: Retorna el resultado formateado
- `arbitro_completamente_pagado`: Verifica si el árbitro fue pagado
- `marcar_inasistencia`: Marca inasistencia de un equipo

### Gol
Goles anotados en partidos.

**Campos principales:**
- `jugador`: Jugador que anotó
- `partido`: Partido en el que se anotó
- `minuto`: Minuto del gol
- `autogol`: Indica si fue autogol

### Tarjeta
Registro de tarjetas amarillas y rojas.

**Campos principales:**
- `jugador`: Jugador amonestado
- `partido`: Partido en el que ocurrió
- `tipo`: Tipo de tarjeta (AMARILLA, ROJA)
- `pagada`: Indica si la multa fue pagada
- `suspension_cumplida`: Indica si la suspensión fue cumplida
- `minuto`: Minuto en que se mostró
- `motivo`: Motivo de la tarjeta

**Métodos importantes:**
- `monto_multa`: Retorna el monto de la multa según el tipo

### CambioJugador
Registro de cambios de jugadores durante partidos.

**Campos principales:**
- `partido`: Partido en el que ocurrió
- `jugador_sale`, `jugador_entra`: Jugadores involucrados
- `minuto`: Minuto del cambio

### EventoPartido
Eventos especiales durante partidos.

**Campos principales:**
- `partido`: Partido en el que ocurrió
- `tipo`: Tipo de evento (SUSPENSION, GRESCA, etc.)
- `descripcion`: Descripción del evento
- `minuto`: Minuto en que ocurrió
- `equipo_responsable`: Equipo responsable si aplica

## Modelos de Estadísticas (`estadisticas.py`)

### EstadisticaEquipo
Estadísticas de equipos en el torneo.

**Campos principales:**
- `equipo`, `torneo`: Equipo y torneo
- `partidos_jugados`, `partidos_ganados`, etc.: Estadísticas de partidos
- `goles_favor`, `goles_contra`, `diferencia_goles`: Estadísticas de goles
- `puntos`: Puntos acumulados
- `tarjetas_amarillas`, `tarjetas_rojas`: Estadísticas de tarjetas

**Métodos importantes:**
- `actualizar_estadisticas`: Actualiza todas las estadísticas

### LlaveEliminatoria
Llaves de eliminación directa.

**Campos principales:**
- `fase`: Fase a la que pertenece
- `numero_llave`: Número de llave
- `equipo_1`, `equipo_2`: Equipos participantes
- `partido`: Partido asociado
- `completada`: Indica si está completada

**Métodos importantes:**
- `generar_partido`: Genera el partido para la llave
- `ganador`: Retorna el ganador de la llave

### MejorPerdedor
Tracking de mejores perdedores por grupo.

**Campos principales:**
- `torneo`: Torneo al que pertenece
- `grupo`: Grupo al que pertenece
- `equipo`: Equipo perdedor
- `puntos`, `diferencia_goles`, etc.: Estadísticas para clasificación

### EventoTorneo
Eventos importantes del torneo.

**Campos principales:**
- `torneo`: Torneo al que pertenece
- `tipo`: Tipo de evento (INICIO_INSCRIPCION, etc.)
- `descripcion`: Descripción del evento
- `fecha`: Fecha del evento
- `equipo_involucrado`: Equipo involucrado si aplica
- `datos_adicionales`: Datos adicionales en formato JSON

## Modelos Financieros (`financiero.py`)

### TipoTransaccion
Tipos de transacciones de pago.

| Valor | Descripción |
|-------|-------------|
| abono_inscripcion | Abono a Inscripción |
| pago_arbitro | Pago de Árbitro |
| pago_balon | Pago de Balón |
| multa_amarilla | Multa por Tarjeta Amarilla |
| multa_roja | Multa por Tarjeta Roja |
| ajuste_manual | Ajuste Manual |
| devolucion | Devolución |

### TransaccionPago
Registro detallado de transacciones de pago.

**Campos principales:**
- `equipo`: Equipo que realiza la transacción
- `partido`: Partido asociado si aplica
- `fecha`: Fecha de la transacción
- `tipo`: Tipo de transacción
- `monto`: Monto de la transacción
- `es_ingreso`: Indica si es ingreso o gasto
- `concepto`: Concepto de la transacción
- `tarjeta`, `jugador`: Referencias específicas
- `observaciones`: Observaciones adicionales

**Métodos importantes:**
- `es_ingreso`: Indica si la transacción es un ingreso
- `es_gasto`: Indica si la transacción es un gasto

### PagoArbitro
Pagos realizados a árbitros por equipos.

**Campos principales:**
- `arbitro`: Árbitro que recibe el pago
- `partido`: Partido arbitrado
- `equipo`: Equipo que realiza el pago
- `monto`: Monto del pago
- `pagado`: Indica si fue pagado
- `fecha_pago`: Fecha de pago
- `metodo_pago`: Método utilizado

## Modelos de Participación (`participacion.py`)

### ParticipacionJugador
Registro detallado de participación de jugadores en partidos.

**Campos principales:**
- `partido`: Partido en el que participa
- `jugador`: Jugador que participa
- `es_titular`: Indica si es titular
- `numero_dorsal`: Número de dorsal
- `minuto_entra`, `minuto_sale`: Control de tiempo jugado
- `motivo_salida`: Motivo de la salida si aplica

**Métodos importantes:**
- `validar_limite_cambios`: Valida que no se excedan los cambios
- `minutos_jugados`: Calcula los minutos jugados
- `salio_durante_partido`: Indica si salió antes del final

## Relaciones entre Modelos

### Relaciones Principales

1. **Torneo - Categoría**
   - Un torneo pertenece a una categoría
   - Una categoría puede tener múltiples torneos

2. **Equipo - Torneo - Categoría**
   - Un equipo pertenece a un torneo y una categoría
   - Un torneo puede tener múltiples equipos
   - Una categoría puede tener múltiples equipos

3. **Jugador - Equipo**
   - Un jugador pertenece a un equipo
   - Un equipo puede tener múltiples jugadores

4. **Partido - Equipos**
   - Un partido tiene dos equipos (local y visitante)
   - Un equipo puede participar en múltiples partidos

5. **Partido - Árbitro**
   - Un partido puede tener un árbitro asignado
   - Un árbitro puede arbitrar múltiples partidos

6. **Gol/Tarjeta - Jugador - Partido**
   - Un gol/tarjeta pertenece a un jugador y un partido
   - Un jugador puede tener múltiples goles/tarjetas
   - Un partido puede tener múltiples goles/tarjetas

## Flujo de Datos

1. **Creación de Torneo**
   - Se crea una categoría
   - Se crea un torneo asociado a la categoría
   - Se configuran parámetros (fase de grupos, eliminatorias, etc.)

2. **Inscripción de Equipos**
   - Se registran equipos en el torneo
   - Se asignan a grupos si hay fase de grupos
   - Se registran jugadores para cada equipo

3. **Programación de Partidos**
   - Se crean jornadas (fase de grupos)
   - Se programan partidos entre equipos
   - Se asignan árbitros a los partidos

4. **Desarrollo de Partidos**
   - Se registran participaciones de jugadores
   - Se registran eventos (goles, tarjetas, cambios)
   - Se actualizan estadísticas de equipos

5. **Control Financiero**
   - Se registran transacciones de pago (inscripciones, arbitraje, multas)
   - Se controlan pagos a árbitros
   - Se generan reportes financieros

6. **Fase Eliminatoria**
   - Se clasifican equipos de la fase de grupos
   - Se generan llaves eliminatorias
   - Se programan partidos de eliminación directa
   - Se registra el ganador del torneo

## Consideraciones Técnicas

1. **Validaciones**
   - Cada modelo implementa validaciones específicas para garantizar la integridad de los datos
   - Se utilizan restricciones de unicidad para evitar duplicados
   - Se implementan validaciones personalizadas en los métodos `clean()`

2. **Métodos de Cálculo**
   - Se utilizan propiedades y métodos para cálculos derivados
   - Las estadísticas se actualizan automáticamente al completar partidos

3. **Señales y Triggers**
   - Se utilizan métodos `save()` personalizados para ejecutar lógica adicional
   - Se implementan actualizaciones en cascada para mantener la consistencia

4. **Ordenamiento**
   - Se definen ordenamientos predeterminados para consultas frecuentes
   - Se utilizan índices para optimizar el rendimiento

## Ejemplos de Uso

### Crear un Torneo

```python
categoria = Categoria.objects.create(
    nombre="VARONES",
    costo_inscripcion=100.00,
    multa_amarilla=2.00,
    multa_roja=5.00
)

torneo = Torneo.objects.create(
    nombre="Torneo Apertura 2025",
    categoria=categoria,
    fecha_inicio="2025-06-01",
    tiene_fase_grupos=True,
    numero_grupos=2
)
```

### Registrar un Equipo

```python
dirigente = Dirigente.objects.create(
    nombre="Juan Pérez",
    telefono="0987654321"
)

equipo = Equipo.objects.create(
    nombre="Real Madrid",
    categoria=categoria,
    torneo=torneo,
    dirigente=dirigente,
    grupo="A"
)
```

### Registrar un Jugador

```python
jugador = Jugador.objects.create(
    primer_nombre="Carlos",
    primer_apellido="Gómez",
    cedula="1234567890",
    equipo=equipo,
    numero_dorsal=10,
    posicion="Delantero",
    nivel=Nivel.ALTO
)
```

### Crear un Partido

```python
partido = Partido.objects.create(
    torneo=torneo,
    equipo_1=equipo1,
    equipo_2=equipo2,
    fecha="2025-06-15 15:00:00",
    cancha="Estadio Principal"
)
```

### Registrar un Gol

```python
gol = Gol.objects.create(
    jugador=jugador,
    partido=partido,
    minuto=35
)

# Actualizar marcador
partido.goles_equipo_1 += 1
partido.save()
```

### Actualizar Estadísticas

```python
estadistica = EstadisticaEquipo.objects.get(equipo=equipo, torneo=torneo)
estadistica.actualizar_estadisticas()
```

## Conclusión

El sistema GoolStar proporciona una estructura robusta y modular para la gestión completa de torneos de fútbol. La organización de los modelos facilita el mantenimiento y la extensión del sistema, permitiendo una gestión eficiente de equipos, jugadores, partidos, estadísticas y finanzas.

La modularización implementada mejora significativamente la legibilidad del código y permite un desarrollo más ágil y colaborativo.
