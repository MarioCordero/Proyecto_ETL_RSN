# Guía de Recreación de Dashboards en Apache Superset — RSN

Esta guía documenta paso a paso cómo recrear los 6 dashboards analíticos del proyecto ETL RSN en Apache Superset. Cada sección incluye el SQL del dataset, la configuración exacta del chart y la decisión operativa que habilita.

---

## Prerequisitos

Antes de empezar, asegúrese de que:

- Superset está corriendo en `http://localhost:8088`
- La conexión al Data Warehouse está configurada con el nombre `DW RSN`
- El esquema `dw` es accesible desde SQL Lab

Si alguno de estos puntos no está listo, consulte la sección **5. Configuración Inicial de Superset** de la guía principal.

---

## Flujo general para cada dashboard

Todos los dashboards siguen el mismo flujo de tres pasos:

1. **Crear el Dataset** — ir a SQL Lab, escribir la consulta y guardarla como dataset virtual
2. **Crear el Chart** — seleccionar el tipo de gráfico y configurar las columnas
3. **Agregar al Dashboard** — crear o abrir el dashboard y arrastrar el chart

---

## Dashboard 1 — Mapa de Riesgo por Estación Caída

**Objetivo:** Mostrar las estaciones inactivas geolocalizadas y qué tan peligrosa es el área donde quedaron fuera de servicio, para priorizar el despacho de cuadrillas de mantenimiento.

### Paso 1 — Crear el Dataset

1. Ir a **SQL Lab → SQL Editor**
2. Seleccionar base de datos `DW RSN` y esquema `dw`
3. Ejecutar la siguiente consulta y verificar que retorna datos:

```sql
SELECT 
    e.latitud,
    e.longitud,
    e.codigo_estacion,
    e.canal,
    COUNT(f.id_hecho)  AS historico_sismos_cercanos,
    MAX(f.magnitud)    AS max_mag_historica
FROM dw.dim_estacion e
LEFT JOIN dw.fact_evento_sismico f ON e.id_estacion = f.id_estacion
WHERE e.estado_operativo = 'Inactivo'
GROUP BY e.latitud, e.longitud, e.codigo_estacion, e.canal;
```

4. Hacer clic en **Save Dataset** → nombre: `ds_EstacionesCaidas`

### Paso 2 — Crear el Chart

1. Desde el dataset guardado, hacer clic en **Explore**
2. En **Chart Type**, seleccionar **deck.gl Scatterplot**
3. Configurar el panel **Query**:

| Campo | Valor |
|---|---|
| Longitude & Latitude | `longitud` \| `latitud` |
| Point Size | `max_mag_historica` |
| Row limit | `10000` |

4. Configurar el panel **Map**:

| Campo | Valor |
|---|---|
| Map Style | Topography (OSM) |
| Color Scheme | Reds |
| Extruded | ✅ Activado |

5. Hacer clic en **Update Chart**
6. Guardar con el nombre `Mapa de Riesgo — Estaciones Caídas`

### Decisión operativa

> Un punto rojo grande en la costa indica una estación inactiva en una zona que históricamente registra sismos de alta magnitud. **Enviar cuadrilla de prioridad alta.**

---

## Dashboard 2 — Degradación de Calibración por Canal

**Objetivo:** Detectar qué canal de sensor (BHE, BHN, BHZ, etc.) presenta errores RMS elevados de forma regional, para llevar solo el módulo de reemplazo correcto al campo.

### Paso 1 — Crear el Dataset

1. Ir a **SQL Lab → SQL Editor**
2. Ejecutar:

```sql
SELECT
    e.latitud,
    e.longitud,
    e.codigo_estacion,
    e.canal,
    ROUND(AVG(f.error_rms)::numeric, 5) AS error_promedio,
    COUNT(f.id_hecho)                   AS total_registros
FROM dw.fact_evento_sismico f
JOIN dw.dim_estacion e ON f.id_estacion = e.id_estacion
WHERE f.error_rms IS NOT NULL
GROUP BY e.latitud, e.longitud, e.codigo_estacion, e.canal
HAVING COUNT(f.id_hecho) >= 10;
```

3. Guardar como `ds_DegradacionCanales`

### Paso 2 — Crear el Chart

1. Desde el dataset, hacer clic en **Explore**
2. En **Chart Type**, seleccionar **deck.gl Screen Grid**
3. Configurar el panel **Query**:

| Campo | Valor |
|---|---|
| Longitude & Latitude | `longitud` \| `latitud` |
| Row limit | `10000` |

4. Configurar el panel **Map**:

| Campo | Valor |
|---|---|
| Map Style | Topography (OSM) |
| Grid Size | `20000` (aprox. 20 km — ideal para ver manchas de error regional) |
| Dynamic Aggregation Function | `MAX` |
| Color Scheme | Reds |

5. Hacer clic en **Update Chart**
6. Guardar como `Degradación de Calibración por Canal`

### Paso 3 — Agregar filtro por canal en el Dashboard

Al agregar este chart al dashboard, incluir un componente **Filter Box** vinculado a la columna `canal` del dataset `ds_DegradacionCanales`. Esto permite seleccionar un canal específico (por ejemplo `BHE`) y ver solo la mancha de error correspondiente.

### Decisión operativa

> Seleccionar el canal `BHE` en el filtro. Si aparece una mancha roja intensa en una región, el sensor de banda ancha horizontal Este está degenerado en esa área. **Llevar solo el módulo de reemplazo BHE, no toda la estación.**

---

## Dashboard 3 — Enjambres Sísmicos Históricos (Alerta Temprana Volcánica)

**Objetivo:** Identificar días donde se concentraron muchos sismos pequeños en un mismo punto geográfico — la firma característica de actividad volcánica o falla activándose.

### Paso 1 — Crear el Dataset

1. Ir a **SQL Lab → SQL Editor**
2. Ejecutar:

```sql
SELECT 
    u.latitud,
    u.longitud,
    t.fecha_completa,
    COUNT(f.id_hecho)  AS cantidad_sismos_dia,
    MAX(f.magnitud)    AS max_mag_enjambre
FROM dw.fact_evento_sismico f
JOIN dw.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
JOIN dw.dim_tiempo    t ON f.id_tiempo    = t.id_tiempo
WHERE f.rango_magnitud IN ('Micro', 'Menor')
GROUP BY u.latitud, u.longitud, t.fecha_completa
HAVING COUNT(f.id_hecho) >= 3
ORDER BY cantidad_sismos_dia DESC
LIMIT 15000;
```

> El `HAVING COUNT >= 3` filtra los días con 3 o más sismos pequeños en el mismo punto. El `LIMIT 15000` evita que el navegador colapse con datos masivos.

3. Guardar como `ds_EnjambresSismicos`

### Paso 2 — Crear el Chart

1. Desde el dataset, hacer clic en **Explore**
2. En **Chart Type**, seleccionar **deck.gl 3D Hexagon**
3. Configurar el panel **Query**:

| Campo | Valor |
|---|---|
| Longitude & Latitude | `longitud` \| `latitud` |
| Bubble Size | `cantidad_sismos_dia` |
| Row limit | `15000` |

4. Configurar el panel **Map**:

| Campo | Valor |
|---|---|
| Map Style | Topography (OSM) |
| Color Scheme | Purple-Orange |
| Extruded | ✅ Activado |
| Grid Size | `3000` |

5. Panel **Advanced → JavaScript data interceptor** — pegar el siguiente código para que la altura de los hexágonos represente el promedio real de `cantidad_sismos_dia` y no solo el conteo de puntos:

```javascript
function(data, viewport) {
  data.features = data.features.map(function(hexagon) {
    var valores = hexagon.points.map(function(p) {
      return p[2];
    }).filter(function(v) { return v != null && !isNaN(v); });

    if (valores.length === 0) return hexagon;

    var promedio = valores.reduce(function(a, b) {
      return a + b;
    }, 0) / valores.length;

    hexagon.elevationValue = promedio;
    hexagon.count = valores.length;
    return hexagon;
  });
  return data;
}
```

6. Hacer clic en **Update Chart**
7. Guardar como `Enjambres Sísmicos Históricos`

### Decisión operativa

> Al rotar el mapa 3D, una "aguja" o torre alta y estrecha indica un enjambre concentrado. Revisar la fecha en el tooltip. **Si coincide con actividad volcánica conocida, cruzar con datos de plantas geotérmicas o volcanes cercanos para evaluación de riesgo.**

---

## Dashboard 4 — Topografía de Esfuerzo Tectónico (Subducción 3D)

**Objetivo:** Visualizar la rampa de subducción de la Placa del Coco hundiéndose bajo Costa Rica. Los sismos superficiales (costa Pacífica) aparecen altos en el mapa 3D; los profundos (centro y Caribe) aparecen en el fondo — dibujando la placa hundiéndose.

### Paso 1 — Crear el Dataset

1. Ir a **SQL Lab → SQL Editor**
2. Ejecutar:

```sql
SELECT 
    u.latitud,
    u.longitud,
    f.profundidad_km,
    f.magnitud
FROM dw.fact_evento_sismico f
JOIN dw.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
WHERE f.profundidad_km IS NOT NULL 
  AND f.rango_magnitud IN ('Moderado', 'Fuerte', 'Mayor');
```

3. Guardar como `ds_SubduccionTectonica`

### Paso 2 — Crear el Chart

1. Desde el dataset, hacer clic en **Explore**
2. En **Chart Type**, seleccionar **deck.gl 3D Hexagon**
3. Configurar el panel **Query**:

| Campo | Valor |
|---|---|
| Longitude & Latitude | `longitud` \| `latitud` |
| Bubble Size | `profundidad_km` |
| Row limit | `10000` |

4. Configurar el panel **Map**:

| Campo | Valor |
|---|---|
| Map Style | Topography (OSM) |
| Color Scheme Type | Sequential |
| Color Scheme | Blues |
| Extruded | ✅ Activado |
| Dynamic Aggregation Function | `mean` |

5. Panel **Advanced → JavaScript data interceptor** — este interceptor invierte la profundidad para que los sismos superficiales queden altos y los profundos queden abajo, dibujando la rampa de subducción:

```javascript
function(data, viewport) {
  data.features = data.features.map(function(hexagon) {
    var profundidades = hexagon.points.map(function(p) {
      return p[2];
    }).filter(function(v) { return v != null && !isNaN(v); });

    if (profundidades.length === 0) return hexagon;

    var promedio = profundidades.reduce(function(a, b) {
      return a + b;
    }, 0) / profundidades.length;

    // Invertir: sismos superficiales (10 km) → altura alta
    //           sismos profundos (150 km)     → altura baja
    hexagon.elevationValue = Math.max(0, 150 - promedio);
    hexagon.count = profundidades.length;
    return hexagon;
  });
  return data;
}
```

6. Panel **Advanced → JavaScript tooltip generator** — para ver la profundidad real al hacer hover:

```javascript
function(object) {
  if (!object) return null;
  var pts = object.points || [];
  var profs = pts.map(function(p){ return p[2]; }).filter(Boolean);
  var prom = profs.length
    ? (profs.reduce(function(a,b){return a+b},0)/profs.length).toFixed(1)
    : 'N/A';
  return 'Eventos: ' + pts.length + '\nProfundidad promedio: ' + prom + ' km';
}
```

7. Hacer clic en **Update Chart**
8. Guardar como `Topografía de Subducción 3D`

### Decisión operativa

> Al inclinar el mapa 3D se ve la "cortina" de puntos hundiéndose de oeste a este. Las ciudades directamente sobre los hexágonos más altos (sismos más superficiales) son las de mayor riesgo sísmico inmediato. **Priorizar refuerzo estructural en esas zonas.**

---

## Dashboard 5 — Estaciones Veteranas bajo Fatiga de Material

**Objetivo:** Identificar estaciones activas que han absorbido la mayor cantidad de energía sísmica acumulada a lo largo de su vida útil, para programar mantenimiento preventivo antes de que fallen.

### Paso 1 — Crear el Dataset

1. Ir a **SQL Lab → SQL Editor**
2. Ejecutar:

```sql
SELECT 
    e.latitud,
    e.longitud,
    e.codigo_estacion,
    COUNT(f.id_hecho)                               AS total_golpes_fuertes,
    MAX(f.magnitud)                                 AS max_golpe_recibido,
    ROUND(CAST(SUM(f.magnitud) AS NUMERIC), 2)      AS energia_acumulada_total
FROM dw.dim_estacion e
JOIN dw.fact_evento_sismico f ON e.id_estacion = f.id_estacion
WHERE e.estado_operativo = 'Activo'
  AND f.magnitud >= 4.0
GROUP BY e.latitud, e.longitud, e.codigo_estacion
ORDER BY energia_acumulada_total DESC;
```

> El umbral `magnitud >= 4.0` filtra solo los eventos que generan esfuerzo físico real sobre el hardware (cemento, data-logger, conectores).

3. Guardar como `ds_FatigaEstaciones`

### Paso 2 — Crear el Chart

1. Desde el dataset, hacer clic en **Explore**
2. En **Chart Type**, seleccionar **deck.gl Scatterplot**
3. Configurar el panel **Query**:

| Campo | Valor |
|---|---|
| Longitude & Latitude | `longitud` \| `latitud` |
| Point Size | `max_golpe_recibido` |
| Row limit | `10000` |

4. Configurar el panel **Map**:

| Campo | Valor |
|---|---|
| Map Style | Topography (OSM) |
| Color Scheme | Spectral |
| Extruded | ✅ Activado |

5. Hacer clic en **Update Chart**
6. Guardar como `Fatiga de Material — Estaciones Veteranas`

### Decisión operativa

> Una estación con `energia_acumulada_total` muy alto y `max_golpe_recibido >= 6.0`, aunque figure como `Activo`, es candidata a falla prematura. **Programar mantenimiento preventivo de cimentación y data-logger para el próximo trimestre.**

---

## Dashboard 6 — Puntos Ciegos de la Red (¿Dónde construir nuevas estaciones?)

**Objetivo:** Visualizar las zonas con mayor error de localización RMS, que corresponden a áreas donde la red sísmica tiene cobertura deficiente. Son los candidatos naturales para instalar nuevas estaciones.

### Paso 1 — Crear el Dataset

1. Ir a **SQL Lab → SQL Editor**
2. Ejecutar:

```sql
SELECT 
    u.latitud,
    u.longitud,
    f.error_rms,
    f.magnitud
FROM dw.fact_evento_sismico f
JOIN dw.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
WHERE f.error_rms IS NOT NULL 
  AND f.error_rms > 0;
```

3. Guardar como `ds_PuntosCiegos`

### Paso 2 — Crear el Chart

1. Desde el dataset, hacer clic en **Explore**
2. En **Chart Type**, seleccionar **deck.gl Screen Grid**
3. Configurar el panel **Query**:

| Campo | Valor |
|---|---|
| Longitude & Latitude | `longitud` \| `latitud` |
| Row limit | `10000` |

4. Configurar el panel **Map**:

| Campo | Valor |
|---|---|
| Map Style | Topography (OSM) |
| Grid Size | `15000` (aprox. 15 km por celda) |
| Dynamic Aggregation Function | `MAX` |
| Color Scheme | Reds |

5. Hacer clic en **Update Chart**
6. Guardar como `Puntos Ciegos de la Red RSN`

### Decisión operativa

> Las celdas rojas más intensas son zonas donde los sismos se localizan con mayor error — la red tiene cobertura deficiente ahí. **Priorizar esas coordenadas para la instalación de nuevas estaciones en el plan de expansión de infraestructura.**

---

## Paso final — Armar el Dashboard consolidado

Una vez creados los 6 charts, unirlos en un solo dashboard:

1. Ir a **Dashboards → + Dashboard**
2. Asignar el nombre `RSN — Dashboards Operativos`
3. Desde la pestaña **Charts** del panel derecho, arrastrar al lienzo los 6 charts creados
4. Organizar por grupos temáticos:
   - Fila 1 (ancho completo): `Topografía de Subducción 3D`
   - Fila 2 (mitad + mitad): `Mapa de Riesgo — Estaciones Caídas` | `Fatiga de Material — Estaciones Veteranas`
   - Fila 3 (mitad + mitad): `Enjambres Sísmicos Históricos` | `Puntos Ciegos de la Red RSN`
   - Fila 4 (ancho completo): `Degradación de Calibración por Canal`
5. Agregar un **Filter Box** global vinculado a `fecha_completa` para filtrar por rango de fechas en los charts que lo soporten
6. Hacer clic en **Save**

---

## Referencia rápida de datasets

| Dataset | Tabla principal | Filtro clave |
|---|---|---|
| `ds_EstacionesCaidas` | `dim_estacion` + `fact_evento_sismico` | `estado_operativo = 'Inactivo'` |
| `ds_DegradacionCanales` | `fact_evento_sismico` + `dim_estacion` | `error_rms IS NOT NULL` |
| `ds_EnjambresSismicos` | `fact_evento_sismico` + `dim_ubicacion` + `dim_tiempo` | `rango_magnitud IN ('Micro','Menor')` |
| `ds_SubduccionTectonica` | `fact_evento_sismico` + `dim_ubicacion` | `rango_magnitud IN ('Moderado','Fuerte','Mayor')` |
| `ds_FatigaEstaciones` | `dim_estacion` + `fact_evento_sismico` | `magnitud >= 4.0` |
| `ds_PuntosCiegos` | `fact_evento_sismico` + `dim_ubicacion` | `error_rms > 0` |
