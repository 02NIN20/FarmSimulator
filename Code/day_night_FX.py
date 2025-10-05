from pyray import *

def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)

def _smoothstep(a: float, b: float, x: float) -> float:
    if a == b:
        return 0.0
    t = _clamp01((x - a) / (b - a))
    return t * t * (3 - 2 * t)

class DayNightFX:
    """
    Filtro simple: overlay de color que simula noche/día según day_fraction (0..1).
    - Día: transparente
    - Noche: tinte (azul oscuro por defecto)
    - Amanecer/atardecer: transición suave
    """

    def __init__(self) -> None:
        # Tramos del día
        self.dawn_start  = 0.20
        self.day_start   = 0.26
        self.dusk_start  = 0.72
        self.night_start = 0.80

        # Tinte nocturno (ajústalo a negro si quieres: Color(0,0,0,220))
        self.night_tint = Color(0, 0, 20, 200)
        self.gain = 1.0

        self._overlay = Color(0, 0, 0, 0)

    def update(self, dt: float, day_fraction: float) -> None:
        t = day_fraction % 1.0
        if t < self.dawn_start:
            darkness = 1.0
        elif t < self.day_start:
            darkness = 1.0 - _smoothstep(self.dawn_start, self.day_start, t)
        elif t < self.dusk_start:
            darkness = 0.0
        elif t < self.night_start:
            darkness = _smoothstep(self.dusk_start, self.night_start, t)
        else:
            darkness = 1.0

        a = int(self.night_tint.a * darkness * self.gain)
        self._overlay = Color(self.night_tint.r, self.night_tint.g, self.night_tint.b, a)

    def draw(self, screen_w: int, screen_h: int) -> None:
        # ¡Dibujar fuera de begin_mode_2d / end_mode_2d!
        if self._overlay.a > 0:
            draw_rectangle(0, 0, screen_w, screen_h, self._overlay)