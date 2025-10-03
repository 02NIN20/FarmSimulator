# zones_geometry.py
from __future__ import annotations
from typing import List, Tuple
import math
import random

Point = Tuple[float, float]

# =========================
# Utilidades de forma/ruido
# =========================

def _sign_pow(x: float, p: float) -> float:
    """f(x)=sign(x)*|x|^p  (p<1 redondea, p>1 cuadradiza)."""
    if x == 0.0:
        return 0.0
    s = 1.0 if x >= 0.0 else -1.0
    return s * (abs(x) ** p)

def _wrap_angle(t: float) -> float:
    """Envuelve [0, 2π)."""
    twopi = 2.0 * math.pi
    t = t % twopi
    if t < 0.0:
        t += twopi
    return t

def _cos_window(theta: float, center: float, width: float) -> float:
    """
    Ventana suave tipo Hann centrada en 'center' con semiancho 'width' (en radianes).
    Retorna 0 fuera del rango, y en [0,1] dentro del rango.
    """
    d = abs(_wrap_angle(theta - center))
    # Mínima distancia circular
    d = min(d, 2.0 * math.pi - d)
    if d >= width:
        return 0.0
    # Hann: 0.5 * (1 + cos(pi * d/width))
    return 0.5 * (1.0 + math.cos(math.pi * d / max(1e-9, width)))

def _multi_sine(theta: float, freqs: List[int], phases: List[float], amps: List[float]) -> float:
    """Suma de senos con frecuencias/ fases/ amplitudes."""
    v = 0.0
    for f, ph, a in zip(freqs, phases, amps):
        v += a * math.sin(f * theta + ph)
    return v

def _chaikin_once(poly: List[Point]) -> List[Point]:
    """Una pasada de Chaikin para suavizar picos sin perder el contorno orgánico."""
    n = len(poly)
    if n < 3:
        return poly[:]
    out: List[Point] = []
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        # r y q (0.25 y 0.75) – orden r luego q
        rx = x0 * 0.75 + x1 * 0.25
        ry = y0 * 0.75 + y1 * 0.25
        qx = x0 * 0.25 + x1 * 0.75
        qy = y0 * 0.25 + y1 * 0.75
        out.append((rx, ry))
        out.append((qx, qy))
    return out

def _normalize_unit_bbox(poly: List[Point]) -> List[Point]:
    """Normaliza el polígono a caja 0..1 × 0..1 (manteniendo proporciones)."""
    minx = min(p[0] for p in poly); maxx = max(p[0] for p in poly)
    miny = min(p[1] for p in poly); maxy = max(p[1] for p in poly)
    w = max(1e-9, maxx - minx); h = max(1e-9, maxy - miny)
    return [((p[0] - minx) / w, (p[1] - miny) / h) for p in poly]

def _make_coast_shape(
    target_vertices: int,
    seed: int,
    # Super-óvalo base
    axis_x: float, axis_y: float,
    round_x: float, round_y: float,
    # Ruido multi-frecuencia
    base_freqs: List[int], base_amp: float,
    detail_freqs: List[int], detail_amp: float,
    # Sesgo direccional (más entrantes en un sector)
    bias_center: float,      # radianes
    bias_width: float,       # radianes
    bias_gain: float,        # multiplica amplitud en esa zona
    # Afinado final
    smooth_passes: int = 1
) -> List[Point]:
    """
    Genera una "costa" orgánica cerrada:
    - Super-óvalo anisotrópico (axis_x/axis_y, redondez round_x/round_y)
    - Ondas multi-frecuencia (senos) para bahías/penínsulas
    - Ventana direccional para enfatizar una región (fiordos, península)
    - Suavizado leve (Chaikin) y normalización 0..1
    """
    random.seed(seed)
    twopi = 2.0 * math.pi

    # Fases aleatorias estables por seed
    base_phases  = [random.uniform(0, twopi) for _ in base_freqs]
    detail_phases= [random.uniform(0, twopi) for _ in detail_freqs]

    # Amplitudes base (disminuyen con la frecuencia)
    base_amps   = [base_amp  / (i + 1) for i in range(len(base_freqs))]
    detail_amps = [detail_amp/ (i + 1) for i in range(len(detail_freqs))]

    # Muestra uniforme en ángulo
    N = int(max(8, min(1000, target_vertices)))
    pts: List[Point] = []

    for i in range(N):
        t = i / float(N)
        th = t * twopi

        # Super-óvalo (como superellipse), usando sign_pow para ajustar "redondez"
        cx = _sign_pow(math.cos(th), round_x) * axis_x
        sy = _sign_pow(math.sin(th), round_y) * axis_y

        # Ruido multi-frecuencia (dos capas)
        w = _cos_window(th, bias_center, bias_width)  # 0..1
        # Amplitud total en esta dirección
        amp_here = 1.0 + w * (bias_gain - 1.0)

        # Sumatoria de senos (base + detalle fino)
        n1 = _multi_sine(th, base_freqs, base_phases, base_amps)
        n2 = _multi_sine(th, detail_freqs, detail_phases, detail_amps)
        noise = amp_here * (n1 + n2)  # puede ser positivo o negativo

        # Factor radial (clamp para evitar “pinchar” al centro)
        radial = 1.0 + noise
        radial = max(0.55, min(1.35, radial))

        x = cx * radial
        y = sy * radial
        pts.append((x, y))

    # Suavizado leve (quita picos muy finos)
    for _ in range(max(0, smooth_passes)):
        pts = _chaikin_once(pts)

    # Normaliza a 0..1
    return _normalize_unit_bbox(pts)

# =========================
# Zonas (presets artísticos)
# =========================

def zone2_alaska_polygon(target_vertices: int = 128) -> List[Point]:
    """
    ZONA 1 → Escenario 2 — Alaska (Valle Matanuska-Susitna)
    - Más “fiordos” hacia el Noroeste (bias_center≈140°)
    - Más alargado horizontalmente
    """
    target_vertices = int(max(80, min(200, target_vertices)))
    return _make_coast_shape(
        target_vertices=target_vertices,
        seed=42,
        axis_x=1.00, axis_y=0.78,      # elipse más ancha
        round_x=0.85, round_y=0.90,    # redondez suave (p<1 redondea)
        base_freqs=[2, 3, 4, 5], base_amp=0.12,
        detail_freqs=[7, 8, 11, 13], detail_amp=0.06,
        bias_center=math.radians(140.0), bias_width=math.radians(85.0), bias_gain=1.8,
        smooth_passes=1
    )

def zone3_ppr_polygon(target_vertices: int = 128) -> List[Point]:
    """
    ZONA 2 → Escenario 3 — Dakota del Norte (Prairie Pothole Region)
    - Óvalo con “scallops” homogéneos (lagunitas), menos agresivo
    """
    target_vertices = int(max(80, min(200, target_vertices)))
    return _make_coast_shape(
        target_vertices=target_vertices,
        seed=73,
        axis_x=0.95, axis_y=0.85,      # óvalo suave
        round_x=0.92, round_y=0.92,
        base_freqs=[2, 3, 4], base_amp=0.09,
        detail_freqs=[6, 9, 12], detail_amp=0.045,
        bias_center=math.radians(45.0), bias_width=math.radians(70.0), bias_gain=1.2,
        smooth_passes=1
    )

def zone4_michigan_polygon(target_vertices: int = 128) -> List[Point]:
    """
    ZONA 3 → Escenario 4 — Michigan (Suttons Bay – Leelanau Peninsula)
    - Más alargado verticalmente, con un “gancho” suave hacia el NE
    """
    target_vertices = int(max(80, min(200, target_vertices)))
    return _make_coast_shape(
        target_vertices=target_vertices,
        seed=101,
        axis_x=0.78, axis_y=1.00,      # más alto que ancho
        round_x=0.88, round_y=0.82,    # algo más puntiagudo vertical
        base_freqs=[2, 3, 5], base_amp=0.10,
        detail_freqs=[7, 10, 14], detail_amp=0.05,
        bias_center=math.radians(20.0), bias_width=math.radians(70.0), bias_gain=1.6,
        smooth_passes=1
    )
