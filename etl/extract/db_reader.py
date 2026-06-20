"""
=============================================================================
Proyecto ETL RSN — Extract Layer: Lector de BD relacional (Fase 3)
=============================================================================
Responsabilidad: Leer la fuente relacional de estaciones sismológicas
(contenedor postgres_RDB, esquema `rdb`) y retornar las estaciones con su canal.

Fuente:
  - rdb.estaciones    : una fila por estación (codigo_red, codigo_estacion, lat/lon).
  - rdb.instrumentos  : una fila por estación+canal (canal, descripción, periodo).

Cada fila resultante corresponde al grano de dw.dim_estacion (estación + canal).
El estado operativo se deriva: si el instrumento no tiene fecha de fin de
mediciones, se considera "Activo"; de lo contrario, "Inactivo".

Seguridad:
  - Consulta de solo lectura, parametrizada por el driver psycopg2.
=============================================================================
"""

from etl.config import get_logger, get_rdb_connection

logger = get_logger("etl.extract.rdb")

# DISTINCT ON garantiza una fila por (estación, canal); el ORDER BY prioriza
# el periodo activo (fin_mediciones NULL) para derivar el estado operativo.
_QUERY = """
    SELECT DISTINCT ON (i.codigo_estacion, i.canal)
        e.codigo_red,
        e.codigo_estacion,
        i.canal,
        COALESCE(NULLIF(TRIM(i.descripcion), ''), 'Desconocido') AS descripcion_sensor,
        e.latitud,
        e.longitud,
        CASE WHEN i.fin_mediciones IS NULL THEN 'Activo' ELSE 'Inactivo' END AS estado_operativo
    FROM rdb.instrumentos i
    JOIN rdb.estaciones e ON e.codigo_estacion = i.codigo_estacion
    ORDER BY i.codigo_estacion, i.canal, i.fin_mediciones ASC NULLS FIRST;
"""


def read_stations() -> list[dict]:
    """Retorna la lista de estaciones+canal desde la BD relacional."""
    estaciones: list[dict] = []
    with get_rdb_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(_QUERY)
            columnas = [desc[0] for desc in cur.description]
            for fila in cur.fetchall():
                estaciones.append(dict(zip(columnas, fila)))

    logger.info("RDB: %d estaciones (estación+canal) leídas", len(estaciones))
    return estaciones