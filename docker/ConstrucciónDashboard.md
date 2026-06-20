### 1. Inversión a Largo Plazo (Justificar presupuesto)

El objetivo es demostrar el crecimiento histórico en la capacidad de detección.

**Paso A: La consulta en SQL Lab**
Copie la siguiente consulta, ejecútela en el editor y guárdela mediante el botón **Save Dataset** con el nombre `ds_historico_inversion`.

```sql
SELECT 
    t.anio,
    COUNT(f.id_hecho) AS eventos_detectados,
    MAX(f.magnitud) AS sismo_mayor
FROM dw.fact_evento_sismico f
JOIN dw.dim_tiempo t ON f.id_tiempo = t.id_tiempo
GROUP BY t.anio
ORDER BY t.anio ASC;
```

**Paso B: Configuración de Gráficos**

* **Gráfico Principal (Line Chart):** Utilice el nuevo dataset. Asigne `anio` en el eje X (Time Column) y `SUM(eventos_detectados)` en la métrica. Esto mostrará la tendencia de detección a lo largo de las décadas.
* **Big Number:** Cree un gráfico de tipo *Big Number* utilizando el mismo dataset. Seleccione la métrica `SUM(eventos_detectados)` sin agrupar por año y asigne el título: *"Eventos detectados desde el inicio del programa"*.

---

### 2. Tablero de Salud de la Red (Mantenimiento)

El objetivo es identificar las estaciones inactivas que limitan la cobertura de la red.

**Paso A: La consulta en SQL Lab**
Ejecute la siguiente consulta y guárdela como `ds_salud_estaciones`.

```sql
SELECT 
    e.codigo_red,
    e.codigo_estacion,
    e.estado_operativo,
    e.descripcion_sensor,
    COUNT(f.id_hecho) AS carga_historica_eventos
FROM dw.fact_evento_sismico f
JOIN dw.dim_estacion e ON f.id_estacion = e.id_estacion
GROUP BY e.codigo_red, e.codigo_estacion, e.estado_operativo, e.descripcion_sensor
ORDER BY carga_historica_eventos DESC;
```

**Paso B: Configuración de Gráficos**

* **Scorecard (Pie Chart / Dona):** Agrupe por `estado_operativo` y utilice `COUNT(codigo_estacion)` como métrica. Esto proporcionará el porcentaje de la red que se encuentra inactiva.
* **Ranking Crítico (Table):** Cree un gráfico de tabla con las columnas de estación y `carga_historica_eventos`. En la sección de filtros (Filters) del menú izquierdo, agregue la condición `estado_operativo = 'Inactivo'`. Esto generará una lista de las estaciones de alto impacto que requieren mantenimiento prioritario.

---

### 3. Alerta de Cambio de Actividad (Vigilancia)

El propósito es detectar desviaciones recientes en la actividad sísmica comparadas con el comportamiento histórico.

**Paso A: La consulta en SQL Lab**
Guarde esta consulta como `ds_vigilancia_zonas`.

```sql
SELECT 
    t.fecha_completa,
    u.zona_geografica,
    COUNT(f.id_hecho) AS sismos_diarios
FROM dw.fact_evento_sismico f
JOIN dw.dim_tiempo t ON f.id_tiempo = t.id_tiempo
JOIN dw.dim_ubicacion u ON f.id_ubicacion = u.id_ubicacion
GROUP BY t.fecha_completa, u.zona_geografica;
```

**Paso B: Configuración de Gráficos**

* **Evolución (Time-series Bar Chart):** Configure el eje X con `fecha_completa` (agrupada por mes) y utilice la métrica `SUM(sismos_diarios)`. Agrupe (Dimensions) por `zona_geografica`.
* **Comparativa Histórica:** En la configuración del gráfico, acceda a la sección **Advanced Analytics**. Configure el *Time Shift* en `1 year ago`. Esto añadirá una línea comparativa sobre el gráfico actual, facilitando la identificación de anomalías o enjambres sísmicos respecto al mismo periodo del año anterior.

---

### 4. Análisis Geoespacial para Nuevas Estaciones (deck.gl)

Al carecer de un motor geoespacial puro para calcular distancias, el indicador **`error_rms`** sirve como proxy. Un error RMS sistemáticamente alto en una zona con alta incidencia sísmica es un fuerte indicador de un área de baja cobertura de triangulación.

**Paso A: La consulta en SQL Lab**
Guarde esta consulta como `ds_puntos_ciegos_rms`.

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

**Paso B: Configuración del Gráfico (deck.gl 3D Hexagon)**
Para generar esta visualización tridimensional:

1. Cree un nuevo gráfico y seleccione **deck.gl 3D Hexagon**.
2. **Longitude & Latitude:** Seleccione las columnas respectivas.
3. **Extrusion (Altura en 3D):** Habilite esta opción utilizando la métrica `COUNT(magnitud)`. Las áreas más elevadas indicarán una mayor concentración de eventos sísmicos.
4. **Color:** Seleccione como métrica de color `AVG(error_rms)`.
5. **Ajustes visuales:** Configure el radio (Radius) a aproximadamente 5000 metros.

**Interpretación de Resultados:**
Al navegar el mapa en 3D (rotando con *Shift* + Clic), los hexágonos con mayor altura y tonalidades oscuras representarán zonas con alta densidad de sismos y un alto promedio de error RMS, señalando ubicaciones óptimas para considerar la instalación de nuevas estaciones de monitoreo.