"""
=============================================================================
Proyecto ETL RSN — Extract Layer (Fase 3)
=============================================================================
Responsabilidad: Leer el archivo fuente Catalogo_RSN_v2022.txt (TSV) y
retornar los registros crudos como una lista de diccionarios.

Notas del formato (verificado sobre el archivo real):
  - Codificación: UTF-16 LE con BOM.
  - Delimitador: tabulador.
  - Columnas: Num, year, month, day, hour, minute, second, RMS,
    longitude, latitude, depth, magnitude.

Seguridad:
  - El path del archivo se recibe como parámetro, nunca desde input del usuario.
  - Se valida que el path resuelto esté dentro del directorio permitido para
    prevenir ataques de path traversal (CWE-22).
  - No se usan funciones de ejecución de sistema operativo.
=============================================================================
"""

import csv
from pathlib import Path

from etl.config import PROJECT_ROOT, get_logger

logger = get_logger("etl.extract.csv")

# El catálogo solo puede leerse desde el directorio de datos del proyecto.
ALLOWED_BASE = (PROJECT_ROOT / "data").resolve()

# Codificación y delimitador del catálogo de la RSN.
ENCODING = "utf-16"
DELIMITER = "\t"


def _validate_path(file_path: str) -> Path:
    """Resuelve el path y verifica que esté dentro de ALLOWED_BASE (anti path-traversal)."""
    resolved = Path(file_path).resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"No existe el archivo fuente: {resolved}")
    if ALLOWED_BASE not in resolved.parents:
        raise ValueError(
            f"Path no permitido: {resolved}. Debe estar dentro de {ALLOWED_BASE}."
        )
    return resolved


def read_catalog(file_path: str) -> list[dict]:
    """
    Lee el catálogo sísmico (TSV UTF-16) y retorna una lista de diccionarios crudos.

    Cada diccionario usa las columnas del encabezado como llaves. No se realiza
    ninguna conversión de tipos aquí; eso es responsabilidad de la capa Transform.
    """
    path = _validate_path(file_path)
    registros: list[dict] = []

    with open(path, encoding=ENCODING, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=DELIMITER)
        for row in reader:
            # Saltar filas en blanco (a veces el TSV trae líneas vacías al final).
            if not row or all((v or "").strip() == "" for v in row.values()):
                continue
            registros.append(row)

    logger.info("CSV: %d registros leídos desde %s", len(registros), path.name)
    return registros
