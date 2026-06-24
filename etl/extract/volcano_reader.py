"""
=============================================================================
Proyecto ETL RSN — Extract Layer: Lector de volcanes (Fase 4)
=============================================================================
Responsabilidad: Leer la fuente de datos maestros de volcanes activos de
Costa Rica (data/volcanes_cr.csv) y retornarla como lista de diccionarios.

Formato:
  - CSV UTF-8 separado por comas.
  - Columnas: codigo_volcan, nombre, latitud, longitud, radio_influencia_km,
    tipo_manifestacion.

Fuente de los datos:
  - Coordenadas: Smithsonian Global Volcanism Program (volcano.si.edu).
  - Monitoreo / clasificación de manifestaciones: OVSICORI-UNA y RSN-UCR.

Seguridad:
  - El path se valida contra el directorio de datos del proyecto (anti
    path-traversal, CWE-22), igual que el lector del catálogo.
=============================================================================
"""

import csv
from pathlib import Path

from etl.config import PROJECT_ROOT, get_logger

logger = get_logger("etl.extract.volcan")

ALLOWED_BASE = (PROJECT_ROOT / "data").resolve()
DEFAULT_PATH = ALLOWED_BASE / "volcanes_cr.csv"


def _validate_path(file_path: Path) -> Path:
    """Resuelve el path y verifica que esté dentro de ALLOWED_BASE (anti path-traversal)."""
    resolved = Path(file_path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"No existe el archivo de volcanes: {resolved}")
    if ALLOWED_BASE != resolved.parent and ALLOWED_BASE not in resolved.parents:
        raise ValueError(f"Path no permitido: {resolved}. Debe estar dentro de {ALLOWED_BASE}.")
    return resolved


def read_volcanoes(file_path=DEFAULT_PATH) -> list[dict]:
    """Lee el CSV de volcanes y retorna una lista de diccionarios crudos."""
    path = _validate_path(file_path)
    volcanes: list[dict] = []
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not row or not (row.get("codigo_volcan") or "").strip():
                continue
            volcanes.append(row)
    logger.info("Volcanes: %d registros leídos desde %s", len(volcanes), path.name)
    return volcanes
