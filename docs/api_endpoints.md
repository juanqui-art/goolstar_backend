# Documentación de Endpoints API – GoolStar

Esta documentación describe los endpoints REST más relevantes para consultar información de torneos en el sistema GoolStar.

---

## 1. Listar torneos activos

**GET** `/api/torneos/activos/`

**Descripción:** Devuelve todos los torneos activos (en curso, no finalizados), ordenados por fecha de inicio (descendente).

**Ejemplo de respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Torneo Clausura 2025",
    "categoria": 2,
    "categoria_nombre": "Varones",
    "fecha_inicio": "2025-05-01",
    "fecha_fin": null,
    "activo": true,
    "finalizado": false,
    "total_equipos": 10
  },
  {
    "id": 2,
    "nombre": "Torneo Apertura Damas 2025",
    "categoria": 1,
    "categoria_nombre": "Damas",
    "fecha_inicio": "2025-04-15",
    "fecha_fin": "2025-06-30",
    "activo": true,
    "finalizado": false,
    "total_equipos": 8
  }
]
```

---

## 2. Detalle de un torneo

**GET** `/api/torneos/{id}/`

**Descripción:** Devuelve los datos completos de un torneo específico, incluyendo información adicional como cantidad de equipos y partidos.

**Ejemplo de respuesta:**
```json
{
  "id": 1,
  "nombre": "Torneo Clausura 2025",
  "categoria": {
    "id": 2,
    "nombre": "Varones",
    "descripcion": "Categoría masculina"
  },
  "fecha_inicio": "2025-05-01",
  "fecha_fin": null,
  "activo": true,
  "finalizado": false,
  "tiene_fase_grupos": true,
  "tiene_eliminacion_directa": true,
  "fase_actual": "grupos",
  "total_equipos": 10,
  "total_partidos": 45,
  "partidos_jugados": 20,
  "partidos_pendientes": 25
}
```

---

## 3. Tabla de posiciones de un torneo

**GET** `/api/torneos/{id}/tabla_posiciones/`

**Parámetros opcionales:**
- `grupo`: Filtra por grupo específico (ej: `A`, `B`, etc.). El valor es sensible a mayúsculas y se convertirá a mayúscula internamente.

**Descripción:** Devuelve la tabla de posiciones del torneo, ordenada por puntos (descendente), diferencia de goles y goles a favor.

**Ejemplo de respuesta:**
```json
{
  "grupo": "A",
  "equipos": [
    {
      "id": 5,
      "equipo": 5,
      "equipo_nombre": "Los Halcones",
      "torneo": 1,
      "puntos": 12,
      "partidos_jugados": 5,
      "partidos_ganados": 4,
      "partidos_empatados": 0,
      "partidos_perdidos": 1,
      "goles_favor": 15,
      "goles_contra": 7,
      "diferencia_goles": 8,
      "tarjetas_amarillas": 3,
      "tarjetas_rojas": 0
    },
    {
      "id": 6,
      "equipo": 6,
      "equipo_nombre": "Real Madrid",
      "torneo": 1,
      "puntos": 10,
      "partidos_jugados": 5,
      "partidos_ganados": 3,
      "partidos_empatados": 1,
      "partidos_perdidos": 1,
      "goles_favor": 10,
      "goles_contra": 5,
      "diferencia_goles": 5,
      "tarjetas_amarillas": 4,
      "tarjetas_rojas": 0
    }
  ]
}
```

---

## 4. Estadísticas generales de un torneo

**GET** `/api/torneos/{id}/estadisticas/`

**Descripción:** Devuelve estadísticas agregadas del torneo, incluyendo totales de equipos, partidos, goles, tarjetas, y equipos destacados.

**Ejemplo de respuesta:**
```json
{
  "torneo": {
    "id": 1,
    "nombre": "Torneo Clausura 2025",
    "categoria": 2,
    "categoria_nombre": "Varones",
    "fecha_inicio": "2025-05-01",
    "fecha_fin": null,
    "activo": true,
    "finalizado": false,
    "total_equipos": 10
  },
  "estadisticas_generales": {
    "total_equipos": 10,
    "total_partidos": 45,
    "partidos_jugados": 20,
    "partidos_pendientes": 25,
    "total_goles": 55,
    "promedio_goles_por_partido": 2.75,
    "tarjetas_amarillas": 8,
    "tarjetas_rojas": 1
  },
  "mejores_equipos": {
    "equipo_mas_goleador": {
      "nombre": "Los Halcones",
      "goles": 15
    },
    "equipo_menos_goleado": {
      "nombre": "Los Tigres",
      "goles_en_contra": 3
    }
  }
}
```

---

## 5. Listar equipos de un torneo

**GET** `/api/equipos/`

**Parámetros opcionales:**
- `torneo`: ID del torneo para filtrar sus equipos (ej: `?torneo=1`)

**Descripción:** Devuelve la lista de equipos, con la posibilidad de filtrar por torneo.

**Ejemplo de respuesta:**
```json
[
  {
    "id": 5,
    "nombre": "Los Halcones",
    "categoria": 2,
    "categoria_nombre": "Varones",
    "grupo": "A",
    "torneo": 1,
    "activo": true
  },
  {
    "id": 6,
    "nombre": "Real Madrid",
    "categoria": 2,
    "categoria_nombre": "Varones",
    "grupo": "A",
    "torneo": 1,
    "activo": true
  }
]
```

---

## 6. Partidos de una jornada

**GET** `/api/partidos/por_jornada/?jornada_id={id}`

**Descripción:** Devuelve los partidos correspondientes a una jornada específica.

**Ejemplo de respuesta:**
```json
[
  {
    "id": 15,
    "equipo_1": 5,
    "equipo_1_nombre": "Los Halcones",
    "equipo_2": 6,
    "equipo_2_nombre": "Real Madrid",
    "jornada": 3,
    "jornada_nombre": "Jornada 3 - Grupo A",
    "fecha": "2025-05-15T15:00:00Z",
    "completado": true,
    "goles_equipo_1": 2,
    "goles_equipo_2": 1,
    "ganador": 5
  },
  {
    "id": 16,
    "equipo_1": 7,
    "equipo_1_nombre": "Barcelona",
    "equipo_2": 8,
    "equipo_2_nombre": "Juventus",
    "jornada": 3,
    "jornada_nombre": "Jornada 3 - Grupo A",
    "fecha": "2025-05-15T17:00:00Z",
    "completado": false,
    "goles_equipo_1": null,
    "goles_equipo_2": null,
    "ganador": null
  }
]
```

---

## Consideraciones de rendimiento

- **Prevención de consultas N+1**: Los endpoints utilizan `select_related` y otras optimizaciones para minimizar consultas a la base de datos.
- **Ordenamiento eficiente**: La tabla de posiciones se ordena por múltiples criterios (puntos, diferencia de goles, goles a favor).
- **Carga de datos bajo demanda**: Los endpoints solo cargan la información necesaria para cada consulta.
- **Manejo de casos borde**: La API maneja casos como torneos sin equipos o partidos sin completar.

## Notas adicionales
- Todos los endpoints devuelven datos en formato JSON.
- Los endpoints pueden ser consultados sin autenticación (por ahora).
- Las fechas se devuelven en formato ISO 8601 (YYYY-MM-DD).
- Puedes probar estos endpoints desde Postman, curl o cualquier frontend que desees construir.
