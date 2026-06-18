"""
=============================================================================
Proyecto ETL RSN — Configuración compartida
=============================================================================
Centraliza:
  - Carga de variables de entorno (.env)
  - Construcción de conexiones psycopg2 al DW y a la BD relacional (RDB)
  - Configuración del logger del pipeline

Seguridad:
  - Las credenciales se leen SIEMPRE desde variables de entorno, nunca del código.
  - No se imprime ninguna credencial en los logs.
=============================================================================
"""

import logging
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Raíz del proyecto (…/Proyecto_ETL_RSN). Este archivo vive en etl/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Cargar el .env de la raíz del proyecto si existe.
load_dotenv(PROJECT_ROOT / ".env")


def _require(name: str, default: str | None = None) -> str:
    """Lee una variable de entorno; falla con mensaje claro si falta y no hay default."""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(
            f"Falta la variable de entorno requerida: {name}. "
            f"Copie .env.example a .env y complete los valores."
        )
    return value


def get_dw_connection():
    """Conexión al Data Warehouse (esquema estrella `dw`)."""
    return psycopg2.connect(
        host=_require("DW_DB_HOST", "127.0.0.1"),
        port=_require("DW_DB_PORT", "5432"),
        dbname=_require("DW_DB_NAME"),
        user=_require("DW_DB_USER"),
        password=_require("DW_DB_PASSWORD"),
    )


def get_rdb_connection():
    """Conexión a la base de datos relacional de estaciones (FDSN)."""
    return psycopg2.connect(
        host=_require("RDB_DB_HOST", "127.0.0.1"),
        port=_require("RDB_DB_PORT", "5433"),
        dbname=_require("RDB_DB_NAME"),
        user=_require("RDB_DB_USER"),
        password=_require("RDB_DB_PASSWORD"),
    )


def get_logger(name: str = "etl") -> logging.Logger:
    """Logger con formato uniforme para todo el pipeline."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
