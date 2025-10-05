# nubladoFX.py
from pyray import *
import random
import math
import sys

class NubladoFX:
    """Sombras de nubes que se mueven con el viento, en coordenadas de mundo."""

    MAX_CLOUD_COUNT = 500            # límite razonable
    BASE_GEN_RATE   = 1.0           # base para probabilidad de spawn
    SPEED_PIXELS    = 10.0          # factor para convertir m/s a px/s (sensación)

    def __init__(self, screen_w: int, screen_h: int) -> None:
        # Tamaño de referencia (solo por compatibilidad con reconstrucción)
        self.width  = int(screen_w)
        self.height = int(screen_h)

        # Estado
        self.clouds: list[dict] = []

        # Viento (rad/s)
        self.wind_angle = 0.0  # radianes
        self.wind_speed = 0.0  # m/s

        # Viewport mundo (x, y, w, h). Por defecto: 0..screen
        self._vx, self._vy = 0.0, 0.0
        self._vw, self._vh = float(max(1, screen_w)), float(max(1, screen_h))

    # ---------------- API pública ----------------
    def set_viewport(self, x: float, y: float, w: float, h: float) -> None:
        """Define el rectángulo visible de la cámara en coords de mundo."""
        self._vx, self._vy = float(x), float(y)
        self._vw, self._vh = max(1.0, float(w)), max(1.0, float(h))

    def resize(self, screen_w: int, screen_h: int) -> None:
        """Opcional: si cambias resolución, puedes notificar aquí."""
        self.width  = int(max(1, screen_w))
        self.height = int(max(1, screen_h))
        # No cambiamos viewport aquí; lo setea game.py cada frame.

    # ---------------- Núcleo ----------------
    def _create_cloud(self, x: float, y: float) -> dict:
        """
        Crea una nube compuesta por varios círculos grises translúcidos.
        Los radios/offsets se eligen aleatoriamente dentro de un rango bonito.
        """
        parts = []
        blobs = random.randint(3, 6)
        base_r = random.uniform(90.0, 170.0)
        alpha  = random.randint(40, 95)

        for _ in range(blobs):
            ang = random.uniform(0.0, 2.0 * math.pi)
            dist= random.uniform(0.0, base_r * 0.45)
            r   = base_r * random.uniform(0.55, 1.15)
            parts.append({
                "offset_x": math.cos(ang) * dist,
                "offset_y": math.sin(ang) * dist,
                "radius":   r,
                "base_alpha": alpha
            })

        return {"x": float(x), "y": float(y), "circles": parts, "alpha": 1.0}

    def _is_off_screen(self, c: dict) -> bool:
        """Fuera del viewport (con margen por radio mayor)."""
        if not c["circles"]:
            return True
        margin = max(p["radius"] for p in c["circles"])
        x0, y0 = self._vx - margin, self._vy - margin
        x1, y1 = self._vx + self._vw + margin, self._vy + self._vh + margin
        return (c["x"] < x0 or c["x"] > x1 or c["y"] < y0 or c["y"] > y1)

    def update(self, frame_time: float, cloudiness: float, wind_speed: float, wind_angle: float) -> None:
        """
        - cloudiness: 0..1
        - wind_speed: m/s (lo convertimos a px/s con SPEED_PIXELS)
        - wind_angle: radianes (0 = derecha, pi/2 = abajo, etc.)
        """
        self.wind_speed = float(wind_speed)
        self.wind_angle = float(wind_angle)

        # 1) Mover nubes existentes
        vx = self.wind_speed * math.cos(self.wind_angle) * self.SPEED_PIXELS
        vy = self.wind_speed * math.sin(self.wind_angle) * self.SPEED_PIXELS
        step_x = vx * frame_time
        step_y = vy * frame_time

        alive = []
        for c in self.clouds:
            c["x"] += step_x
            c["y"] += step_y
            if not self._is_off_screen(c):
                alive.append(c)
        self.clouds = alive

        # 2) Spawnear nubes nuevas en el viewport
        if cloudiness > 0.0 and len(self.clouds) < self.MAX_CLOUD_COUNT:
            # Prob. simple de spawn por frame (escalada por nubosidad)
            gen_rate = self.BASE_GEN_RATE * max(0.05, min(1.0, cloudiness))
            # Espera ~1/gen_rate segundos por nube de media
            if random.random() < gen_rate * frame_time:
                x = random.uniform(self._vx, self._vx + self._vw)
                y = random.uniform(self._vy, self._vy + self._vh)
                self.clouds.append(self._create_cloud(x, y))

    def draw(self) -> None:
        """
        Dibujo de las sombras de nubes. Debe llamarse dentro de begin_mode_2d().
        """
        for c in self.clouds:
            if c["alpha"] <= sys.float_info.epsilon:
                continue
            for part in c["circles"]:
                a = int(max(0, min(255, part["base_alpha"] * c["alpha"])))
                draw_circle(
                    int(c["x"] + part["offset_x"]),
                    int(c["y"] + part["offset_y"]),
                    float(part["radius"]),
                    Color(120, 120, 120, a)   # gris suave
                )
