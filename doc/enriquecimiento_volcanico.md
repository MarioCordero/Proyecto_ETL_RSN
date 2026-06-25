# Enriquecimiento de Datos Volcánicos (Sismo ↔ Volcán)

Documento de respaldo para fundamentar, **con datos reales**, el cruce entre microsismos y
volcanes activos de Costa Rica. Reúne los tres entregables: (1) la fuente de datos maestros,
(2) las sentencias DDL, y (3) la lógica de transformación.

---

## Fuentes de datos (para citar)

- **Coordenadas de los volcanes:** Smithsonian Institution — *Global Volcanism Program* (GVP),
  Volcanoes of the World. https://volcano.si.edu/
- **Monitoreo y tipo de manifestación:** *Observatorio Vulcanológico y Sismológico de Costa Rica*
  (OVSICORI-UNA, https://www.ovsicori.una.ac.cr/) y *Red Sismológica Nacional* (RSN, UCR-ICE,
  https://rsn.ucr.ac.cr/).
- El radio de influencia (10 km) es un **supuesto del proyecto** para asociar sismicidad de flanco
  al edificio volcánico; es un parámetro configurable por volcán en la fuente.

---

## Tarea 1 — Dataset origen (datos maestros)

Archivo: `data/volcanes_cr.csv` (UTF-8, separado por comas). 10 volcanes activos/monitoreados.

| codigo_volcan | nombre | latitud | longitud | radio_influencia_km | tipo_manifestacion |
|---|---|---|---|---|---|
| POAS | Volcán Poás | 10.200000 | -84.233000 | 10 | Emisión de gases (SO2) / Erupción freática |
| IRAZU | Volcán Irazú | 9.979000 | -83.852000 | 10 | Fumarolas / Deslizamientos |
| TURRI | Volcán Turrialba | 10.025000 | -83.767000 | 10 | Emisión de gases (SO2) / Erupción freática |
| ARENAL | Volcán Arenal | 10.463000 | -84.703000 | 10 | Erupción estromboliana (en reposo desde 2010) |
| RINCON | Volcán Rincón de la Vieja | 10.830000 | -85.324000 | 10 | Erupción freática / Lahares |
| MIRAV | Volcán Miravalles | 10.748000 | -85.153000 | 10 | Fumarolas / Actividad geotérmica |
| TENOR | Volcán Tenorio | 10.673000 | -85.015000 | 10 | Fumarolas / Aguas termales |
| BARVA | Volcán Barva | 10.135000 | -84.100000 | 10 | Fumarolas (latente) |
| PLATA | Volcán Platanar | 10.300000 | -84.366000 | 10 | Fumarolas (latente) |
| OROSI | Volcán Orosí | 10.980000 | -85.473000 | 10 | Fumarolas (latente) |

> Nota de modelado: el prompt original pedía un campo `id_volcan`; en el DW ese nombre se reserva
> para la **clave subrogada UUID** de la dimensión, por lo que la llave de negocio del archivo se
> llama `codigo_volcan` (mismo patrón que `codigo_estacion` en `dim_estacion`).

---

## Tarea 2 — DDL (PostgreSQL)

Idéntico a `db/migration_dim_volcan.sql` (idempotente, no rompe lo existente).

```sql
-- 1. Nueva dimensión de volcanes
CREATE TABLE IF NOT EXISTS dw.dim_volcan (
    id_volcan UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo_volcan VARCHAR(10) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    latitud NUMERIC(9, 6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9, 6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    radio_influencia_km NUMERIC(5, 2) NOT NULL DEFAULT 10 CHECK (radio_influencia_km > 0),
    tipo_manifestacion VARCHAR(100) NOT NULL DEFAULT 'Desconocido',
    CONSTRAINT uq_dim_volcan UNIQUE (codigo_volcan)
);

-- 2. Llave foránea al volcán cercano en la tabla de hechos (NULLABLE)
ALTER TABLE dw.fact_evento_sismico
    ADD COLUMN IF NOT EXISTS id_volcan_cercano UUID
    REFERENCES dw.dim_volcan(id_volcan) ON DELETE SET NULL;

-- 3. Índice
CREATE INDEX IF NOT EXISTS idx_fact_id_volcan
    ON dw.fact_evento_sismico(id_volcan_cercano);
```

---

## Tarea 3 — Lógica de transformación (Python / Pandas)

Versión **autónoma** con Pandas + Numpy (para el informe). En el pipeline real la misma lógica está
integrada con la librería estándar reutilizando `haversine()` de `etl/transform/cleaner.py`
(función `_nearest_volcano_within_radius`).

```python
import numpy as np
import pandas as pd


def _haversine_km(lat1, lon1, lat2, lon2):
    """Distancia haversine en km. Acepta escalares o arrays de numpy."""
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def asignar_volcan_cercano(df_sismos: pd.DataFrame, df_volcanes: pd.DataFrame) -> pd.DataFrame:
    """
    Para cada sismo, asigna el `codigo_volcan` del volcán más cercano cuya distancia al epicentro
    sea <= su `radio_influencia_km`. Si ninguno cumple, queda NaN (sismo NO volcánico).

    df_sismos   : columnas 'latitud', 'longitud' (epicentro).
    df_volcanes : columnas 'codigo_volcan', 'latitud', 'longitud', 'radio_influencia_km'.
    """
    df = df_sismos.copy()
    df["codigo_volcan"] = np.nan

    v_lat = df_volcanes["latitud"].to_numpy(dtype=float)
    v_lon = df_volcanes["longitud"].to_numpy(dtype=float)
    v_cod = df_volcanes["codigo_volcan"].to_numpy()
    v_rad = df_volcanes["radio_influencia_km"].to_numpy(dtype=float)

    for i, row in df.iterrows():
        dist = _haversine_km(row["latitud"], row["longitud"], v_lat, v_lon)  # vector vs todos los volcanes
        dentro = dist <= v_rad                                               # máscara: dentro del radio
        if dentro.any():
            validos = np.where(dentro)[0]
            mejor = validos[np.argmin(dist[validos])]                        # el más cercano que cumple
            df.at[i, "codigo_volcan"] = v_cod[mejor]
    return df


# Alternativa con Geopy (mayor precisión geodésica), reemplazando _haversine_km:
#   from geopy.distance import geodesic
#   dist = np.array([geodesic((row.latitud, row.longitud), (vl, vo)).km
#                    for vl, vo in zip(v_lat, v_lon)])
```

---

## Resultado verificado (carga real)

- **10** volcanes cargados en `dw.dim_volcan`.
- **4 994** eventos asociados a un volcán (dentro de los 10 km); **85 348** quedan `NULL` (no volcánicos).
- Microsismos (`rango_magnitud = 'Micro'`) correctamente marcados por volcán
  (p. ej. Miravalles 266, Rincón de la Vieja 50, Tenorio 39, Irazú 34, Turrialba 28, Poás 27).

Consulta de comprobación:

```sql
SELECT v.nombre, v.tipo_manifestacion,
       COUNT(*) AS eventos,
       COUNT(*) FILTER (WHERE f.rango_magnitud = 'Micro') AS microsismos
FROM dw.fact_evento_sismico f
JOIN dw.dim_volcan v ON v.id_volcan = f.id_volcan_cercano
GROUP BY v.nombre, v.tipo_manifestacion
ORDER BY eventos DESC;
```
