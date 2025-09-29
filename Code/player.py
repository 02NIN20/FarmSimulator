from __future__ import annotations
import math
from typing import Dict, Tuple, Optional
from pyray import *

class Player:
    """Jugador con ease-in/out en aceleración (versión simple)."""

    def __init__(self, start_pos: Vector2, size: int = 32, speed: float = 100, accel_time: float = 0.15) -> None:
        self.position = Vector2(start_pos.x, start_pos.y)
        self.size = size
        self.speed = speed
        self._dir = Vector2(0.0, 0.0)
        self._progress = 0.0
        self.accel_time = max(1e-4, accel_time)
        self._velocity = Vector2(0.0, 0.0)

    @staticmethod
    def _length(v: Vector2) -> float:
        return math.hypot(v.x, v.y)

    @staticmethod
    def _normalize(v: Vector2) -> Vector2:
        l = Player._length(v)
        if l > 1e-9:
            return Vector2(v.x / l, v.y / l)
        return Vector2(0.0, 0.0)

    @staticmethod
    def _dot(a: Vector2, b: Vector2) -> float:
        return a.x * b.x + a.y * b.y

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Función de easing para suavizar el movimiento."""
        if t <= 0.0: return 0.0
        if t >= 1.0: return 1.0
        return t * t * (3.0 - 2.0 * t)

    def update(self, move_axis: Vector2, dt: float) -> None:

        """Actualiza posición a partir de un vector de movimiento normalizado."""
        self.position.x += move_axis.x * self.speed * dt
        self.position.y += move_axis.y * self.speed * dt

        mag = Player._length(move_axis)
        moving = mag > 1e-6

        if moving:
            new_dir = Player._normalize(move_axis)
            # Detección de cambio de dirección para resetear el ease-in
            if Player._length(self._dir) > 1e-6 and Player._dot(new_dir, self._dir) < 0.7:
                self._progress = 0.0
            self._dir = new_dir
            self._progress += dt / self.accel_time
        else:
            self._progress -= dt / self.accel_time

        self._progress = max(0.0, min(1.0, self._progress))
        speed_mult = Player.ease_in_out(self._progress)
        
        # Calcular nueva velocidad
        vx = self._dir.x * self.speed * speed_mult
        vy = self._dir.y * self.speed * speed_mult
        self._velocity.x = vx
        self._velocity.y = vy

        # Aplicar movimiento
        self.position.x += vx * dt
        self.position.y += vy * dt

    def draw(self) -> None:
        # Dibuja un simple cuadrado centrado en self.position
        x = int(self.position.x - self.size / 2)
        y = int(self.position.y - self.size / 2)
        draw_rectangle(x, y, self.size, self.size, Color(200, 50, 50, 255))
