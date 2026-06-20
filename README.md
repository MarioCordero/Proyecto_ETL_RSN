# Proyecto ETL RSN — Data Warehouse Sísmico

Pipeline **ETL (Extract – Transform – Load)** que integra **tres fuentes de datos en formatos distintos** sobre sismicidad en Costa Rica y las carga en un **Data Warehouse PostgreSQL con esquema estrella**, listo para dashboards y reportes.

> Curso CI-0141 Bases de Datos Avanzadas — ECCI, Universidad de Costa Rica.


## Fuentes de datos (3 formatos)

<dd>

| # | Formato | Fuente | Origen |
|---|---------|--------|--------|
| 1 | CSV / texto (TSV, UTF-16) | Catálogo histórico de sismos de la **RSN** (1975–2022) | `https://rsn.ucr.ac.cr/images/Sismologia/Catalogo_RSN_v2022.txt` |
| 2 | API REST (GeoJSON) | Eventos recientes del **USGS**, filtrados al bounding box de Costa Rica | `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| 3 | Base de datos relacional | Inventario de **estaciones e instrumentos** (redes RSN-`TC` y OVSICORI-`OV`) | **IRIS FDSN** (`service.iris.edu/fdsnws/station`), cargado en PostgreSQL |

Los eventos (CSV + API) **no traen código de estación**, por lo que cada evento se une con la **estación más cercana** (distancia haversine) de la fuente relacional. Ese es el punto donde las 3 fuentes se integran.

</dd>

## Arquitectura

<dd>

```
  FUENTES                 EXTRACT              TRANSFORM                 LOAD              DATA WAREHOUSE
┌────────────┐       ┌────────────────┐                                                 ┌──────────────────┐
│ Catálogo   │─────▶│ reader.py      │─┐                                               │  esquema dw      │
│ RSN (CSV)  │       │ (TSV UTF-16)   │ │                                               │ ──────────────── │
├────────────┤       ├────────────────┤ │    ┌────────────────────┐    ┌────────────┐   │ fact_evento_…    │
│ USGS (API) │─────▶│ api_client.py  │ ├──▶│ cleaner.py         │──▶│ loader.py  │─▶│ dim_tiempo       │
│ GeoJSON    │       │ (paginación)   │ │    │ normaliza · limpia │    │ surrogate  │   │ dim_ubicacion    │
├────────────┤       ├────────────────┤ │    │ deduplica          │    │ keys ·     │   │ dim_estacion     │
│ Estaciones │─────▶│ db_reader.py   │─┘    │ enriquece          │    │ full /     │   │ etl_auditoria    │
│ (BD rel.)  │       │ (PostgreSQL)   │      │ + estación cercana │    │ incremental│   │ (rango_magnitud  │
│            │       │                │      │                    │    │            │   │  en el hecho)    │
└────────────┘       └────────────────┘      └────────────────────┘    └────────────┘   └──────────────────┘
```

Capas (spec §6.1): **Extracción** → conectores por formato · **Transformación** → limpieza/validación/normalización/enriquecimiento/conformado · **Carga** → inserción en el modelo dimensional · **Presentación** → Superset (fase posterior).

</dd>

## Estructura del proyecto

<dd>

```
Proyecto_ETL_RSN/
├── docker/
│   └── docker-compose.yml      # PostgreSQL DW + PostgreSQL relacional + pgAdmin + Superset
├── db/
│   ├── init.sql                # DDL del DW: esquema estrella + auditoría (autoejecutado)
│   └── init-2.sql              # DDL de la BD relacional: estaciones + instrumentos
├── data/
│   ├── stations_sites.txt      # Estaciones (FDSN, nivel station) — versionado
│   ├── stations_channel.txt    # Canales/instrumentos (FDSN, nivel channel) — versionado
│   └── raw/
│       └── Catalogo_RSN_v2022.txt  # Catálogo CSV (NO versionado; se descarga)
├── etl/
│   ├── pipeline.py             # Orquestador (CLI)
│   ├── config.py               # Conexiones (DW/RDB) + logging desde .env
│   ├── requirements.txt
│   ├── extract/
│   │   ├── reader.py           # CSV (TSV UTF-16 + guard anti path-traversal)
│   │   ├── api_client.py       # API USGS (paginación + reintentos)
│   │   └── db_reader.py        # BD relacional (estaciones ⋈ instrumentos)
│   ├── transform/
│   │   └── cleaner.py          # Normaliza, limpia, deduplica y enriquece
│   └── load/
│       └── loader.py           # Get-or-create de dimensiones + carga de hechos
├── .env.example
└── README.md
```

</dd>

## Puesta en marcha

### En linux/Mac

<dd>

  #### 1. Variables de entorno
  ```bash
  cp .env.example .env
  # Edite credenciales si lo desea. Los puertos del host (DW_DB_PORT / RDB_DB_PORT)
  # son configurables: cámbielos si 5432/5433 ya están ocupados en su máquina.
  ```

  #### 2. Levantar las bases de datos
  ```bash
  cd docker
  docker compose --env-file ../.env up -d # Puede necesitar permisos de super usuario (sudo)
  docker compose --env-file ../.env ps          # ambos deben quedar "healthy"
  ```
  El DW ejecuta `db/init.sql` (esquema estrella) y la BD relacional ejecuta `db/init-2.sql` (carga las estaciones) automáticamente en el primer arranque.

  #### 3. Dependencias de Python
  ```bash
  cd ..                       # volver a la raíz del proyecto (salir de docker/)
  python3 -m venv .venv
  .venv/bin/pip install -r etl/requirements.txt
  ```
  > Todos los comandos de Python (pasos 3 a 5) se ejecutan desde la **raíz del proyecto**, no desde `docker/`.

  #### 4. Descargar el catálogo CSV
  ```bash
  mkdir -p data/raw
  curl -L -o data/raw/Catalogo_RSN_v2022.txt \
    https://rsn.ucr.ac.cr/images/Sismologia/Catalogo_RSN_v2022.txt
  ```

  #### 5. Ejecutar el pipeline
  ```bash
  # Carga completa (las 3 fuentes)
  .venv/bin/python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt
  ```

</dd>

## Uso del CLI

<dd>

```bash
python -m etl.pipeline --file <ruta> [opciones]
```

| Opción | Descripción |
|--------|-------------|
| `--file` | Ruta al catálogo CSV/TSV (obligatorio, dentro de `data/`). |
| `--source {all,csv,api}` | Fuentes de eventos a procesar (default: `all`). |
| `--skip-api` | Omite la API USGS (equivale a `--source csv`). |
| `--incremental` | Solo agrega hechos nuevos (no recarga todo). |
| `--dry-run` | Ejecuta Extract + Transform **sin escribir** en la BD. |

- **Carga completa** (sin `--incremental`): trunca y recarga la tabla de hechos → **idempotente** (correrla N veces da el mismo resultado).
- **Carga incremental** (`--incremental`): inserta solo eventos que aún no existen (p. ej. para traer sismos recientes del USGS).

</dd>


## Esquema estrella (DW)

<dd>

```
        dim_tiempo
   (anio,mes,dia,hora)
            │
            ▼
   ┌─────────────────────────────────────────────────────┐
   │                fact_evento_sismico                  │
   │  magnitud · profundidad_km · error_rms              │
   │  rango_magnitud (clasificación como atributo)       │
   └─────────────────────────────────────────────────────┘
            ▲                        ▲
            │                        │
       dim_ubicacion            dim_estacion
     (latitud,longitud)     (codigo_estacion,canal)
```

- **3 dimensiones**: `dim_tiempo`, `dim_ubicacion`, `dim_estacion`.
- **Claves subrogadas** (UUID) en todas las dimensiones; **llaves naturales** con restricción `UNIQUE` que habilitan el *get-or-create*.
- La **clasificación de magnitud** (`rango_magnitud`: Micro … Mayor) vive como **atributo del hecho** (degenerate dimension), no como dimensión propia; se deriva en la transformación.
- `dw.etl_auditoria` registra, por corrida y fuente, cuántos registros se extrajeron, cargaron y descartaron.

</dd>


## Cómo verificar que funciona

<dd>

```bash
# Conteos del DW
docker exec rsn_postgres_dw psql -U etl_user -d rsn_dw -c \
"SELECT (SELECT COUNT(*) FROM dw.fact_evento_sismico) AS hechos,
        (SELECT COUNT(*) FROM dw.dim_estacion) AS estaciones;"

# Bitácora de auditoría
docker exec rsn_postgres_dw psql -U etl_user -d rsn_dw -c \
"SELECT fuente, rows_extraidas, rows_cargadas, rows_descartadas FROM dw.etl_auditoria ORDER BY ejecutado_en;"

# Idempotencia: una segunda carga incremental debe insertar 0
.venv/bin/python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt --incremental
```

</dd>

## Detener / limpiar

<dd>

```bash
cd docker
docker compose --env-file ../.env stop        # detener (conserva datos)
docker compose --env-file ../.env down        # eliminar contenedores (conserva volúmenes)
docker compose --env-file ../.env down -v     # eliminar TODO, incl. datos (cuidado)
```

</dd>

## Requisitos

<dd>

| Herramienta | Versión |
|-------------|---------|
| Docker / Compose | 24.x / v2 |
| Python | 3.11+ (probado en 3.13) |
| psycopg2-binary | 2.9.10 |
| requests | 2.32.3 |
| python-dotenv | 1.0.1 |

</dd>