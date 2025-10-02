# zones_geometry.py
from __future__ import annotations
from typing import List, Tuple

Point = Tuple[float, float]

def zone2_alaska_polygon() -> List[Point]:
    """
    Alaska (Valle Matanuska-Susitna) – silueta estilizada en coordenadas normalizadas (0..1).
    """
    return [
        (0.10, 0.20), (0.18, 0.12), (0.32, 0.10), (0.45, 0.15),
        (0.55, 0.10), (0.68, 0.14), (0.78, 0.22), (0.86, 0.32),
        (0.90, 0.44), (0.86, 0.58), (0.78, 0.66), (0.67, 0.73),
        (0.58, 0.78), (0.46, 0.82), (0.34, 0.78), (0.26, 0.70),
        (0.22, 0.62), (0.18, 0.53), (0.16, 0.46), (0.12, 0.35),
    ]

def zone3_ppr_polygon() -> List[Point]:
    """
    Dakota del Norte — Prairie Pothole Region (contorno ovalado-dentado).
    """
    return [
        (0.20, 0.18), (0.32, 0.12), (0.46, 0.12), (0.58, 0.16),
        (0.70, 0.22), (0.80, 0.34), (0.84, 0.46), (0.82, 0.58),
        (0.74, 0.70), (0.62, 0.78), (0.48, 0.82), (0.36, 0.80),
        (0.26, 0.72), (0.18, 0.62), (0.14, 0.50), (0.16, 0.36),
    ]

def zone4_michigan_polygon() -> List[Point]:
    """
    Michigan — Leelanau Peninsula (semi-península alargada).
    """
    return [
        (0.30, 0.15), (0.42, 0.12), (0.54, 0.16), (0.62, 0.22),
        (0.68, 0.30), (0.70, 0.40), (0.68, 0.52), (0.62, 0.62),
        (0.54, 0.70), (0.44, 0.76), (0.34, 0.78), (0.24, 0.74),
        (0.20, 0.64), (0.22, 0.52), (0.24, 0.40), (0.26, 0.28),
    ]
