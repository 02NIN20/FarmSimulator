# automatic_query.py
from __future__ import annotations
import os, csv, glob, math, hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------------- Config ----------------
_OUTPUT_DIRS: List[Path] = [
    Path(__file__).parent / "output_consultas",
    Path.cwd() / "output_consultas",
]
_WIND_MIN, _WIND_MAX = 0.5, 8.0

# Estado “actual” (lo setea game.py según la escena)
_CURRENT_STATE: str = "CA"

def set_current_state(state_abbrev: str) -> None:
    """Define el estado (CA/AK/ND/MI, etc.) contra el que se leerán los CSV."""
    global _CURRENT_STATE
    if isinstance(state_abbrev, str) and len(state_abbrev) in (2,3):
        _CURRENT_STATE = state_abbrev.upper()

# --------------- Utils ------------------
def _hashf(s: str) -> float:
    h = hashlib.sha256(s.encode()).hexdigest()
    return int(h[:12], 16) / float(16**12)

def _clamp(x: float, a: float, b: float) -> float:
    return a if x < a else b if x > b else x

def _soft_rain_norm(mm: float) -> float:
    if mm is None: return 0.0
    try: mm = float(mm)
    except Exception: return 0.0
    # Normalización suave: 0mm→0, ~8mm→0.63, 20mm→0.86, 40mm→0.98
    return 1.0 - math.exp(-mm / 8.0)

def _list_state_files(state: str) -> List[Path]:
    patt = f"{state.upper()}_*_consulta.csv"
    files: List[Path] = []
    for base in _OUTPUT_DIRS:
        files.extend([Path(p) for p in glob.glob(str(base / patt))])
    return files

def _read_csv_all(path: Path) -> List[dict]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def _parse_int(x) -> Optional[int]:
    try: return int(str(x))
    except Exception: return None

def _row_date_key(r: dict) -> Optional[int]:
    """
    Devuelve un entero YYYYMMDD desde columnas comunes si existen.
    Se intentan: PrecipDate, SatelliteDate, TargetDate. Si no hay,
    devuelve None (ese row quedará al final sin ordenar estricta).
    """
    for k in ("PrecipDate", "SatelliteDate", "TargetDate"):
        v = _parse_int(r.get(k))
        if v: return v
    return None

# --------------- Carga + Index por “día N” ---------------
# Memo: state -> lista de rows ordenada por fecha (o en el orden que venga si no hay fecha)
_ROWS_BY_STATE: Dict[str, List[dict]] = {}

def _ensure_rows_loaded_for_state(state: str) -> List[dict]:
    state = state.upper()
    if state in _ROWS_BY_STATE:
        return _ROWS_BY_STATE[state]

    rows: List[dict] = []
    for p in _list_state_files(state):
        rows.extend(_read_csv_all(p))

    # Ordena por fecha si puede; los que no tengan fecha caen al final.
    def _sort_key(r: dict) -> Tuple[int, int]:
        d = _row_date_key(r)
        return (0, d) if d is not None else (1, 99999999)

    rows.sort(key=_sort_key)
    _ROWS_BY_STATE[state] = rows
    return rows

# --------------- Derivación de señales ---------------
def _derive_signals_from_row(state: str, row: dict) -> Dict[str, float]:
    # Lluvia + nubosidad
    precip_mm = row.get("Precipitation_mm")
    rain = _soft_rain_norm(float(precip_mm) if precip_mm not in (None, "") else 0.0)

    none_p = row.get("None_P")
    none_p = float(none_p) if (none_p not in (None, "")) else 50.0
    drought_penalty = 0.0
    for k in ("D2_P", "D3_P", "D4_P"):
        v = row.get(k)
        if v not in (None, ""):
            drought_penalty += float(v)

    cloud = 0.30 + 0.50*rain + 0.20*(1.0 - none_p/100.0)
    cloud = _clamp(cloud, 0.0, 1.0)

    # Viento (si falta, default 2 m/s)
    wspd = row.get("WindSpeed_GLDAS")
    try: wspd = float(wspd)
    except Exception: wspd = 2.0
    wind_speed = _clamp(wspd, _WIND_MIN, _WIND_MAX)

    # Ángulo no viene → estable por hash (para no saltar caóticamente)
    # Usa fecha si existe para que “avance” con el dataset; si no, usa índice virtual 0.
    dkey = _row_date_key(row) or 0
    wind_angle = -math.pi + 2*math.pi*_hashf(f"{state}-{dkey}-wind")

    # Crecimiento de cultivos
    soil = row.get("SoilMoisture_SMAP")
    ndvi = row.get("NDVI_MODIS")
    lst  = row.get("LST_Day_MODIS")

    soil = float(soil) if soil not in (None, "") else 0.30
    ndvi = float(ndvi) if ndvi not in (None, "") else 0.20
    lst  = float(lst)  if lst  not in (None, "") else 295.0  # K (~22°C)

    heat_pen = 0.0
    if lst >= 305.0:  # >32°C
        heat_pen = min(0.2, (lst - 305.0) * 0.02)

    drought_frac = _clamp(drought_penalty/100.0, 0.0, 1.0)

    growth = (
        1.0
        + 0.35*rain
        + 0.25*(soil - 0.30)
        + 0.20*(ndvi - 0.20)
        - 0.30*drought_frac
        - heat_pen
    )
    crop_mul = _clamp(growth, 0.6, 1.8)

    return {
        "rain": float(_clamp(rain, 0.0, 1.0)),
        "cloud": float(cloud),
        "wind_speed_mps": float(wind_speed),
        "wind_angle_rad": float(wind_angle),
        "crop_mul": float(crop_mul),
    }

# --------------- API pedida: SOLO DÍA ---------------
# Memo por (state, day_index)
_MEMO: Dict[Tuple[str, int], Dict[str, float]] = {}

def climate_signals_day(day_index: int) -> Dict[str, float]:
    """
    Devuelve señales climáticas en función del 'día N' (1..∞) y del estado 'actual'
    que se fija con set_current_state(...). Si el día N excede el dataset disponible,
    se cicla: idx = (N-1) % len(rows).
    """
    state = _CURRENT_STATE.upper()
    N = max(1, int(day_index))
    key = (state, N)
    if key in _MEMO:
        return _MEMO[key]

    rows = _ensure_rows_loaded_for_state(state)
    if not rows:
        # Sin datos → fallback determinista estable
        # (usa “fecha virtual” derivada del N)
        y = 2025
        m = ((N-1)//30)%12 + 1
        d = ((N-1)%30) + 1
        r = _derive_signals_from_row(
            state,
            {
                "Precipitation_mm": 0.0 + 12.0*_hashf(f"{state}-p-{N}"),
                "WindSpeed_GLDAS":  1.5 + 5.5*_hashf(f"{state}-w-{N}"),
                "None_P": 60.0,
                "D2_P": 10.0*_hashf(f"{state}-d2-{N}"),
                "D3_P":  5.0*_hashf(f"{state}-d3-{N}"),
                "D4_P":  2.5*_hashf(f"{state}-d4-{N}"),
                "SoilMoisture_SMAP": 0.25 + 0.20*_hashf(f"{state}-s-{N}"),
                "NDVI_MODIS": 0.15 + 0.50*_hashf(f"{state}-n-{N}"),
                "LST_Day_MODIS": 295.0 + 12.0*_hashf(f"{state}-t-{N}"),
                "PrecipDate": int(f"{y:04d}{m:02d}{d:02d}"),
            }
        )
        _MEMO[key] = r
        return r

    idx = (N - 1) % len(rows)
    row = rows[idx]
    out = _derive_signals_from_row(state, row)
    _MEMO[key] = out
    return out
