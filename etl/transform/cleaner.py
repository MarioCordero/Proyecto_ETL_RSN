"""
=============================================================================
Proyecto ETL RSN — Transform Layer (Fase 3)
=============================================================================
Responsabilidad: Limpiar, validar, normalizar y enriquecer los eventos crudos
de las dos fuentes de eventos (CSV catálogo + API USGS) y unirlos con la
fuente relacional (estaciones) vía la estación más cercana.

Pasos:
  1. Normalizar cada fuente a una forma común de evento.
  2. Limpiar/validar: descartar magnitud nula/no numérica, lat/lon fuera de rango.
  3. Deduplicar el solapamiento entre el catálogo histórico y la API.
  4. Enriquecer: rango de magnitud, zona geográfica, día de la semana y la
     estación más cercana (join con la fuente relacional vía haversine).

Supuestos de normalización:
  - El catálogo de la RSN se asume ya en hora local de Costa Rica.
  - Los tiempos de la API USGS vienen en UTC y se convierten a hora local (UTC-6).

Seguridad:
  - Todos los valores se validan antes de usarse; no se usa eval()/exec().
=============================================================================
"""

import math
from datetime import datetime, timedelta, timezone

from etl.config import get_logger

logger = get_logger("etl.transform")

# Costa Rica: UTC-6, sin horario de verano.
CR_TZ = timezone(timedelta(hours=-6))


# --------------------------------------------------------------------------
# Parsers seguros
# --------------------------------------------------------------------------
def _to_float(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def _to_int(value):
    f = _to_float(value)
    return int(f) if f is not None else None


# --------------------------------------------------------------------------
# Enriquecimiento
# --------------------------------------------------------------------------
def clasificar_magnitud(mag: float) -> str:
    """Mapea una magnitud a su rango cualitativo (se guarda como atributo del hecho)."""
    if mag < 2.0:
        return "Micro"
    if mag < 4.0:
        return "Menor"
    if mag < 5.0:
        return "Ligero"
    if mag < 6.0:
        return "Moderado"
    if mag < 7.0:
        return "Fuerte"
    return "Mayor"


def clasificar_zona(lat: float, lon: float) -> str:
    """Clasifica el epicentro en una zona geográfica aproximada de Costa Rica."""
    # Valle Central (área central, más específica → se evalúa primero).
    if 9.7 <= lat <= 10.2 and -84.5 <= lon <= -83.7:
        return "Valle Central"
    # Guanacaste (noroeste).
    if lat >= 10.0 and lon <= -85.0:
        return "Guanacaste"
    # Caribe (este).
    if lon >= -83.5 and lat >= 9.3:
        return "Caribe"
    # Zona Sur (sureste).
    if lat <= 9.5 and lon >= -84.0:
        return "Zona Sur"
    # Pacífico Central (suroeste costero).
    if 9.0 <= lat <= 10.0 and -85.0 <= lon <= -84.0:
        return "Pacífico Central"
    return "Sin clasificar"


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en kilómetros entre dos coordenadas (fórmula de haversine)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _build_station_index(stations: list[dict]) -> list[tuple]:
    """Una ubicación única por estación (codigo_estacion, lat, lon) para el nearest-join."""
    vistos = {}
    for s in stations:
        cod = s["codigo_estacion"]
        if cod not in vistos:
            vistos[cod] = (cod, float(s["latitud"]), float(s["longitud"]))
    return list(vistos.values())


def _nearest_station(lat: float, lon: float, index: list[tuple]) -> str | None:
    """Retorna el codigo_estacion más cercano al epicentro, o None si no hay estaciones."""
    mejor_cod, mejor_dist = None, float("inf")
    for cod, slat, slon in index:
        d = haversine(lat, lon, slat, slon)
        if d < mejor_dist:
            mejor_cod, mejor_dist = cod, d
    return mejor_cod


def _build_volcano_index(volcanes: list[dict]) -> list[tuple]:
    """Lista (codigo_volcan, lat, lon, radio_km) para el cruce sismo↔volcán."""
    index = []
    for v in volcanes:
        cod = (v.get("codigo_volcan") or "").strip()
        lat = _to_float(v.get("latitud"))
        lon = _to_float(v.get("longitud"))
        radio = _to_float(v.get("radio_influencia_km"))
        if cod and lat is not None and lon is not None and radio:
            index.append((cod, lat, lon, radio))
    return index


def _nearest_volcano_within_radius(lat: float, lon: float, index: list[tuple]) -> str | None:
    """
    Retorna el codigo_volcan del volcán más cercano cuya distancia al epicentro sea
    menor o igual a su radio_influencia_km. Si ninguno cumple, retorna None
    (el sismo no se considera asociado a actividad volcánica).
    """
    mejor_cod, mejor_dist = None, float("inf")
    for cod, vlat, vlon, radio in index:
        d = haversine(lat, lon, vlat, vlon)
        if d <= radio and d < mejor_dist:
            mejor_cod, mejor_dist = cod, d
    return mejor_cod


# --------------------------------------------------------------------------
# Normalización por fuente
# --------------------------------------------------------------------------
def _normalize_common(anio, mes, dia, hora, minuto, segundo, lat, lon, depth, mag, rms, source):
    """Valida y construye un evento en la forma común. Retorna None si es inválido."""
    mag = _to_float(mag)
    lat = _to_float(lat)
    lon = _to_float(lon)
    if mag is None or mag < 0:
        return None
    if lat is None or not (-90 <= lat <= 90):
        return None
    if lon is None or not (-180 <= lon <= 180):
        return None
    if None in (anio, mes, dia, hora):
        return None

    depth = _to_float(depth)
    if depth is not None and depth < 0:
        depth = None
    rms = _to_float(rms)
    if rms is not None and rms < 0:
        rms = None

    try:
        dia_semana = datetime(anio, mes, dia).isoweekday()
    except ValueError:
        return None  # fecha inválida (p. ej. día 31 en un mes corto)

    return {
        "anio": anio, "mes": mes, "dia": dia, "hora": hora,
        "minuto": minuto or 0, "segundo": segundo or 0,
        "dia_semana": dia_semana,
        "latitud": round(lat, 6), "longitud": round(lon, 6),
        "profundidad_km": depth,
        "magnitud": round(mag, 2),
        "error_rms": rms,
        "rango_magnitud": clasificar_magnitud(mag),
        "zona_geografica": clasificar_zona(lat, lon),
        "source": source,
    }


def _normalize_csv(row: dict):
    return _normalize_common(
        anio=_to_int(row.get("year")), mes=_to_int(row.get("month")),
        dia=_to_int(row.get("day")), hora=_to_int(row.get("hour")),
        minuto=_to_int(row.get("minute")), segundo=_to_int(row.get("second")),
        lat=row.get("latitude"), lon=row.get("longitude"),
        depth=row.get("depth"), mag=row.get("magnitude"), rms=row.get("RMS"),
        source="CSV",
    )


def _normalize_api(feature: dict):
    props = feature.get("properties", {}) or {}
    coords = (feature.get("geometry", {}) or {}).get("coordinates", []) or []
    if len(coords) < 2 or props.get("time") is None:
        return None
    lon, lat = coords[0], coords[1]
    depth = coords[2] if len(coords) >= 3 else None
    dt = datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc).astimezone(CR_TZ)
    return _normalize_common(
        anio=dt.year, mes=dt.month, dia=dt.day, hora=dt.hour,
        minuto=dt.minute, segundo=dt.second,
        lat=lat, lon=lon, depth=depth,
        mag=props.get("mag"), rms=props.get("rms"),
        source="API",
    )


# --------------------------------------------------------------------------
# Orquestación de la transformación
# --------------------------------------------------------------------------
def _dedup_key(ev: dict) -> tuple:
    """Llave para detectar el mismo sismo entre el catálogo y la API."""
    return (
        ev["anio"], ev["mes"], ev["dia"], ev["hora"], ev["minuto"],
        round(ev["latitud"], 2), round(ev["longitud"], 2),
    )


def transform(csv_rows: list[dict], api_features: list[dict], stations: list[dict],
              volcanes: list[dict] | None = None) -> dict:
    """
    Limpia, deduplica y enriquece los eventos. Retorna:
        {
          "eventos": [ <evento común con estación y volcán asignados> , ... ],
          "stats": { ... métricas por fuente para auditoría ... },
        }
    """
    station_index = _build_station_index(stations)
    volcano_index = _build_volcano_index(volcanes or [])

    stats = {
        "csv_extraidas": len(csv_rows), "csv_descartadas": 0,
        "api_extraidas": len(api_features), "api_descartadas": 0,
        "duplicados": 0,
    }

    eventos: list[dict] = []
    vistos: set[tuple] = set()

    def _procesar(crudos, normalizar, key_desc, key_drop):
        for crudo in crudos:
            ev = normalizar(crudo)
            if ev is None:
                stats[key_drop] += 1
                continue
            k = _dedup_key(ev)
            if k in vistos:
                stats["duplicados"] += 1
                continue
            vistos.add(k)
            eventos.append(ev)

    # El catálogo histórico se procesa primero; la API solo agrega lo que falte.
    _procesar(csv_rows, _normalize_csv, "csv", "csv_descartadas")
    _procesar(api_features, _normalize_api, "api", "api_descartadas")

    # Enriquecimiento final: estación más cercana (join con la fuente relacional).
    if station_index:
        for ev in eventos:
            ev["codigo_estacion"] = _nearest_station(ev["latitud"], ev["longitud"], station_index)
    else:
        logger.warning("No hay estaciones disponibles; los eventos quedarán sin estación.")
        for ev in eventos:
            ev["codigo_estacion"] = None

    # Enriquecimiento: volcán cercano (cruce sismo↔volcán dentro del radio de influencia).
    eventos_volcanicos = 0
    for ev in eventos:
        cod = _nearest_volcano_within_radius(ev["latitud"], ev["longitud"], volcano_index) \
            if volcano_index else None
        ev["codigo_volcan"] = cod
        if cod:
            eventos_volcanicos += 1
    stats["eventos_volcanicos"] = eventos_volcanicos

    stats["total_eventos"] = len(eventos)
    logger.info(
        "Transform: %d eventos válidos (CSV descartó %d, API descartó %d, %d duplicados, "
        "%d asociados a volcán)",
        stats["total_eventos"], stats["csv_descartadas"],
        stats["api_descartadas"], stats["duplicados"], eventos_volcanicos,
    )
    return {"eventos": eventos, "stats": stats}
