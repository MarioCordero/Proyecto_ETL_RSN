"""
=============================================================================
Proyecto ETL RSN — Extract Layer: Cliente API USGS (Fase 3)
=============================================================================
Responsabilidad: Consumir la API REST del USGS (FDSN event service) en formato
GeoJSON, filtrada a la región de Costa Rica, y retornar los eventos crudos.

Estructura de la respuesta:
  features[].properties.{mag, time (epoch ms), rms, place, magType}
  features[].geometry.coordinates = [longitude, latitude, depth_km]

Robustez:
  - Paginación por desplazamiento (offset) respetando el límite del servicio.
  - Reintentos con backoff exponencial ante errores de red/5xx.
  - Timeout en cada request.
=============================================================================
"""

import time

import requests

from etl.config import get_logger

logger = get_logger("etl.extract.api")

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# Bounding box de Costa Rica (de la especificación del proyecto).
CR_BBOX = {
    "minlatitude": 8.0,
    "maxlatitude": 11.5,
    "minlongitude": -86.0,
    "maxlongitude": -82.5,
}

PAGE_SIZE = 1000          # eventos por página (el servicio admite hasta 20000)
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30


def _get_with_retries(params: dict) -> dict:
    """GET a la API con reintentos y backoff exponencial. Retorna el JSON parseado."""
    last_error = None
    for intento in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(USGS_URL, params=params, timeout=TIMEOUT_SECONDS)
            # 204 = sin contenido (no hay más eventos en esta página).
            if resp.status_code == 204:
                return {"features": []}
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            espera = 2 ** intento
            logger.warning(
                "API USGS: intento %d/%d falló (%s). Reintentando en %ds…",
                intento, MAX_RETRIES, exc, espera,
            )
            time.sleep(espera)
    raise RuntimeError(f"API USGS: agotados los reintentos. Último error: {last_error}")


def fetch_events(start_year: int = 1975) -> list[dict]:
    """
    Descarga los eventos sísmicos de la región de Costa Rica desde `start_year`.

    Retorna una lista de diccionarios crudos, cada uno con la forma:
        {"properties": {...}, "geometry": {...}, "id": "..."}
    La normalización a la forma común de evento ocurre en la capa Transform.
    """
    eventos: list[dict] = []
    offset = 1  # el servicio FDSN usa offset basado en 1

    base_params = {
        "format": "geojson",
        "starttime": f"{start_year}-01-01",
        "orderby": "time-asc",
        "limit": PAGE_SIZE,
        **CR_BBOX,
    }

    while True:
        params = {**base_params, "offset": offset}
        data = _get_with_retries(params)
        features = data.get("features", [])
        if not features:
            break

        eventos.extend(features)
        logger.info("API USGS: %d eventos acumulados (offset=%d)", len(eventos), offset)

        if len(features) < PAGE_SIZE:
            break  # última página
        offset += PAGE_SIZE

    logger.info("API USGS: %d eventos descargados en total", len(eventos))
    return eventos
