"""
=============================================================================
Proyecto ETL RSN — Pipeline Principal (Fase 3)
=============================================================================
Orquesta las tres fases: Extract → Transform → Load

Uso:
    python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt
    python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt --dry-run
    python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt --source csv
    python -m etl.pipeline --file data/raw/Catalogo_RSN_v2022.txt --incremental

Fuentes integradas:
    - CSV : catálogo histórico de la RSN (TSV UTF-16).
    - API : eventos recientes del USGS (GeoJSON, bbox de Costa Rica).
    - RDB : estaciones sismológicas (BD relacional), unidas por estación más cercana.

Variables de entorno requeridas (cargadas desde .env):
    DW_DB_*  → Data Warehouse
    RDB_DB_* → Base de datos relacional de estaciones
=============================================================================
"""

import argparse
import sys

from etl.config import get_logger
from etl.extract import api_client, db_reader, reader, volcano_reader
from etl.load.loader import load_to_dw
from etl.transform.cleaner import transform

logger = get_logger("etl.pipeline")


def _parse_args(argv=None):
    p = argparse.ArgumentParser(description="Pipeline ETL RSN — esquema estrella.")
    p.add_argument("--file", required=True,
                   help="Ruta al catálogo CSV/TSV (dentro de data/).")
    p.add_argument("--source", choices=["all", "csv", "api"], default="all",
                   help="Fuentes de eventos a procesar (default: all).")
    p.add_argument("--skip-api", action="store_true",
                   help="Atajo para omitir la API (equivale a --source csv).")
    p.add_argument("--incremental", action="store_true",
                   help="Solo carga hechos que aún no existen en el DW.")
    p.add_argument("--dry-run", action="store_true",
                   help="Ejecuta Extract + Transform sin escribir en la BD.")
    return p.parse_args(argv)


def run(file_path, source="all", skip_api=False, incremental=False, dry_run=False):
    use_csv = source in ("all", "csv")
    use_api = source in ("all", "api") and not skip_api

    # ---- EXTRACT ----------------------------------------------------------
    logger.info("=== EXTRACT ===")
    csv_rows = reader.read_catalog(file_path) if use_csv else []
    api_features = api_client.fetch_events() if use_api else []

    try:
        stations = db_reader.read_stations()
    except Exception as exc:  # la BD relacional puede no estar arriba
        logger.warning("No se pudo leer la BD relacional (%s). Se continúa sin estaciones.", exc)
        stations = []

    try:
        volcanes = volcano_reader.read_volcanoes()
    except Exception as exc:  # la fuente de volcanes es opcional
        logger.warning("No se pudo leer la fuente de volcanes (%s). Se continúa sin volcanes.", exc)
        volcanes = []

    # ---- TRANSFORM --------------------------------------------------------
    logger.info("=== TRANSFORM ===")
    resultado = transform(csv_rows, api_features, stations, volcanes)
    eventos, stats = resultado["eventos"], resultado["stats"]

    # ---- LOAD -------------------------------------------------------------
    if dry_run:
        logger.info("=== DRY-RUN (no se escribe en la BD) ===")
        logger.info("Resumen: %s", stats)
        return {"dry_run": True, "stats": stats}

    logger.info("=== LOAD ===")
    res = load_to_dw(eventos, stations, stats, incremental=incremental, volcanes=volcanes)

    logger.info("=== RESUMEN FINAL ===")
    logger.info("Hechos insertados: %d", res["insertados"])
    logger.info("Conteos del DW: %s", res["conteos"])
    return res


def main(argv=None):
    args = _parse_args(argv)
    try:
        run(
            file_path=args.file,
            source=args.source,
            skip_api=args.skip_api,
            incremental=args.incremental,
            dry_run=args.dry_run,
        )
    except Exception as exc:
        logger.error("El pipeline falló: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
