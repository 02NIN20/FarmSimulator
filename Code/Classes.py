"""Entidades del juego: GameObject, Scene, Box y Player."""

from __future__ import annotations

import math
from pyray import *


class GameObject:
    """Interfaz mínima para objetos que viven dentro de una escena."""

    def update(self, dt: float) -> None:
        """Actualiza el objeto; por defecto no hace nada."""
        return None

    def draw(self) -> None:
        """Dibuja el objeto; por defecto no hace nada."""
        return None


class Box(GameObject):
    """Rectángulo estático de ejemplo (propio de cada escena)."""

    def __init__(self, rect: Rectangle, color: Color) -> None:
        self.rect = rect
        self.color = color

    def update(self, dt: float) -> None:
        return None

    def draw(self) -> None:
        draw_rectangle_rec(self.rect, self.color)
        draw_rectangle_lines_ex(self.rect, 2, BLACK)


class Scene:
    """Contiene el estado y objetos de una escena de juego."""

    def __init__(
        self,
        scene_id: int,
        size: Vector2,
        bg_color: Color,
        spawn: Vector2,
    ) -> None:
        self.id = scene_id
        self.size = size
        self.bg_color = bg_color
        self.spawn = spawn  # posición inicial del jugador en esta escena
        self.objects: list[GameObject] = []

    def add(self, obj: GameObject) -> GameObject:
        self.objects.append(obj)
        return obj

    def update(self, dt: float) -> None:
        for obj in self.objects:
            obj.update(dt)

    def center(self) -> Vector2:
        return Vector2(self.size.x * 0.5, self.size.y * 0.5)

    def draw(self) -> None:
        draw_rectangle(0, 0, int(self.size.x), int(self.size.y), self.bg_color)
        draw_rectangle_lines(0, 0, int(self.size.x), int(self.size.y), BLACK)
        draw_text(f"Escena {self.id}", 12, 12, 24, WHITE)
        for obj in self.objects:
            obj.draw()


class Player:
    """Jugador: un cuadrado que se mueve con un tamaño y velocidad constantes."""

    def __init__(self, start_pos: Vector2, size: int = 32, speed: float = 240.0, accel_time: float = 0.15) -> None:
        self.position = Vector2(start_pos.x, start_pos.y)
        self.size = size
        self.speed = speed

        # Estado para el easing
        self._dir = Vector2(0.0, 0.0)        # dirección de movimiento actual (unit vector)
        self._progress = 0.0                 # 0 = parado, 1 = velocidad máxima
        self.accel_time = max(0.2, accel_time)

        # velocidad actual (opcional, útil para debug)
        self._velocity = Vector2(0.0, 0.0)

    # --- helpers ---
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
        """Smoothstep (ease in/out). t en [0,1]."""
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        return t * t * (3.0 - 2.0 * t)

    def update(self, move_axis: Vector2, dt: float) -> None:
        mag = Player._length(move_axis)
        moving = mag > 1e-6

        if moving:
            new_dir = Player._normalize(move_axis)
            if Player._length(self._dir) > 1e-6 and Player._dot(new_dir, self._dir) < 0.9:
                self._progress = 0.0
            self._dir = new_dir
            self._progress += dt / self.accel_time
        else:
            self._progress -= dt / self.accel_time

        if self._progress < 0.0:
            self._progress = 0.0
        elif self._progress > 1.0:
            self._progress = 1.0

        speed_mult = Player.ease_in_out(self._progress)

        vx = self._dir.x * self.speed * speed_mult
        vy = self._dir.y * self.speed * speed_mult
        self._velocity.x = vx
        self._velocity.y = vy

        self.position.x += vx * dt
        self.position.y += vy * dt

    def draw(self) -> None:
        half = self.size / 2
        rect = Rectangle(self.position.x - half, self.position.y - half, self.size, self.size)
        draw_rectangle_rec(rect, BLACK)
        draw_rectangle_lines_ex(rect, 2, YELLOW)