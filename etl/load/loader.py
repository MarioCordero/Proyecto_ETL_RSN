"""
=============================================================================
Proyecto ETL RSN — Load Layer (Fase 3)
=============================================================================
Responsabilidad: Insertar los eventos transformados en el Data Warehouse
PostgreSQL respetando el esquema estrella, generando claves subrogadas.

Estrategia:
  1. Cargar dim_estacion desde la fuente relacional.
  2. Upsert masivo (execute_values + ON CONFLICT) de dim_tiempo y dim_ubicacion;
     luego construir mapas llave natural → UUID subrogado.
  3. Insertar la tabla de hechos resolviendo las claves foráneas. La clasificación
     de magnitud (rango_magnitud) se guarda como atributo del propio hecho.
  4. Modo incremental: omitir hechos ya presentes (firma natural).
  5. Validación post-carga + escritura de auditoría (dw.etl_auditoria).

Seguridad:
  - TODAS las consultas usan parámetros (psycopg2); nunca concatenación (CWE-89).
  - La conexión se configura desde variables de entorno.
=============================================================================
"""

from psycopg2.extras import execute_values

from etl.config import get_dw_connection, get_logger

logger = get_logger("etl.load")


# --------------------------------------------------------------------------
# Carga de dimensiones
# --------------------------------------------------------------------------
def _load_dim_estacion(cur, stations: list[dict]) -> dict:
    """Inserta las estaciones y retorna el mapa codigo_estacion → id_estacion representativo."""
    if stations:
        execute_values(
            cur,
            """
            INSERT INTO dw.dim_estacion
                (codigo_red, codigo_estacion, descripcion_sensor, canal,
                 latitud, longitud, estado_operativo)
            VALUES %s
            ON CONFLICT (codigo_estacion, canal) DO NOTHING
            """,
            [
                (s["codigo_red"], s["codigo_estacion"], s["descripcion_sensor"],
                 s["canal"], s["latitud"], s["longitud"], s["estado_operativo"])
                for s in stations
            ],
        )
    # Un id representativo por estación (el primer canal en orden) para los hechos.
    cur.execute(
        """
        SELECT DISTINCT ON (codigo_estacion) codigo_estacion, id_estacion
        FROM dw.dim_estacion
        ORDER BY codigo_estacion, canal
        """
    )
    return {cod: sid for cod, sid in cur.fetchall()}


def _upsert_and_map(cur, eventos: list[dict]) -> tuple[dict, dict]:
    """Upsert masivo de tiempo/ubicacion y retorno de sus mapas."""
    # Conjuntos únicos a partir de los eventos.
    tiempos = {(e["anio"], e["mes"], e["dia"], e["hora"]): e["dia_semana"] for e in eventos}
    ubicaciones = {(e["latitud"], e["longitud"]): e["zona_geografica"] for e in eventos}

    if tiempos:
        execute_values(
            cur,
            """INSERT INTO dw.dim_tiempo (anio, mes, dia, hora, dia_semana)
               VALUES %s ON CONFLICT (anio, mes, dia, hora) DO NOTHING""",
            [(a, m, d, h, ds) for (a, m, d, h), ds in tiempos.items()],
        )
    if ubicaciones:
        execute_values(
            cur,
            """INSERT INTO dw.dim_ubicacion (latitud, longitud, zona_geografica)
               VALUES %s ON CONFLICT (latitud, longitud) DO NOTHING""",
            [(lat, lon, zona) for (lat, lon), zona in ubicaciones.items()],
        )
    # Construir los mapas llave natural → UUID.
    cur.execute("SELECT anio, mes, dia, hora, id_tiempo FROM dw.dim_tiempo")
    map_tiempo = {(a, m, d, h): tid for a, m, d, h, tid in cur.fetchall()}

    cur.execute("SELECT latitud, longitud, id_ubicacion FROM dw.dim_ubicacion")
    map_ubic = {(float(lat), float(lon)): uid for lat, lon, uid in cur.fetchall()}

    return map_tiempo, map_ubic


# --------------------------------------------------------------------------
# Incremental
# --------------------------------------------------------------------------
def _existing_signatures(cur) -> set:
    """Firmas naturales de los hechos ya cargados (para la carga incremental)."""
    cur.execute(
        """
        SELECT t.anio, t.mes, t.dia, t.hora, u.latitud, u.longitud, f.magnitud
        FROM dw.fact_evento_sismico f
        JOIN dw.dim_tiempo t   ON t.id_tiempo = f.id_tiempo
        JOIN dw.dim_ubicacion u ON u.id_ubicacion = f.id_ubicacion
        """
    )
    return {
        (a, m, d, h, float(lat), float(lon), float(mag))
        for a, m, d, h, lat, lon, mag in cur.fetchall()
    }


def _signature(ev: dict) -> tuple:
    return (
        ev["anio"], ev["mes"], ev["dia"], ev["hora"],
        float(ev["latitud"]), float(ev["longitud"]), float(ev["magnitud"]),
    )


# --------------------------------------------------------------------------
# Auditoría y validación
# --------------------------------------------------------------------------
def _write_audit(cur, fuente, extraidas, cargadas, descartadas, estado="OK", detalle=""):
    cur.execute(
        """INSERT INTO dw.etl_auditoria
           (fuente, rows_extraidas, rows_cargadas, rows_descartadas, estado, detalle)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (fuente, extraidas, cargadas, descartadas, estado, detalle),
    )


def _validate(cur) -> dict:
    """Conteos post-carga; los FKs garantizan que no haya hechos huérfanos."""
    counts = {}
    for tabla in ("dim_tiempo", "dim_ubicacion", "dim_estacion",
                  "fact_evento_sismico"):
        cur.execute(f"SELECT COUNT(*) FROM dw.{tabla}")
        counts[tabla] = cur.fetchone()[0]
    return counts


# --------------------------------------------------------------------------
# Entrada principal
# --------------------------------------------------------------------------
def load_to_dw(eventos: list[dict], stations: list[dict], stats: dict,
               incremental: bool = False) -> dict:
    """Carga los eventos al DW. Retorna un resumen con conteos y validación."""
    inserted_by_source = {"CSV": 0, "API": 0}

    with get_dw_connection() as conn:
        with conn.cursor() as cur:
            station_map = _load_dim_estacion(cur, stations)
            map_tiempo, map_ubic = _upsert_and_map(cur, eventos)

            # Carga inicial (full load): la tabla de hechos se reemplaza por
            # completo, de modo que volver a correrla es idempotente y no
            # duplica registros. La carga incremental solo agrega lo nuevo.
            if not incremental:
                cur.execute("TRUNCATE dw.fact_evento_sismico")
                logger.info("Full load: tabla de hechos truncada antes de recargar.")

            existentes = _existing_signatures(cur) if incremental else set()

            filas_fact = []
            for ev in eventos:
                if incremental and _signature(ev) in existentes:
                    continue
                filas_fact.append((
                    map_ubic[(float(ev["latitud"]), float(ev["longitud"]))],
                    map_tiempo[(ev["anio"], ev["mes"], ev["dia"], ev["hora"])],
                    station_map.get(ev.get("codigo_estacion")),
                    ev["magnitud"], ev["profundidad_km"], ev["error_rms"],
                    ev["rango_magnitud"],
                ))
                inserted_by_source[ev["source"]] += 1

            if filas_fact:
                execute_values(
                    cur,
                    """INSERT INTO dw.fact_evento_sismico
                       (id_ubicacion, id_tiempo, id_estacion,
                        magnitud, profundidad_km, error_rms, rango_magnitud)
                       VALUES %s""",
                    filas_fact,
                    page_size=1000,
                )

            # Auditoría por fuente.
            _write_audit(cur, "CSV", stats["csv_extraidas"],
                         inserted_by_source["CSV"], stats["csv_descartadas"])
            _write_audit(cur, "API", stats["api_extraidas"],
                         inserted_by_source["API"], stats["api_descartadas"])

            counts = _validate(cur)
        conn.commit()

    logger.info(
        "Load: %d hechos insertados (CSV=%d, API=%d). DW: %d hechos en total.",
        len(filas_fact), inserted_by_source["CSV"], inserted_by_source["API"],
        counts["fact_evento_sismico"],
    )
    return {"insertados": len(filas_fact), "por_fuente": inserted_by_source, "conteos": counts}
