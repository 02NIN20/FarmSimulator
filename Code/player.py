from __future__ import annotations
import math
from typing import Dict, Tuple, Optional
from pyray import *

class Player:

    def __init__(self, start_pos: Vector2, size: int = 32, speed: float = 240.0, accel_time: float = 0.15) -> None:
        self.position = Vector2(start_pos.x, start_pos.y)
        self.size = size
        self.base_speed = speed          # 240.0 por defecto
        self.sprint_speed = speed * 1.8  # ~432.0 (ejemplo: 80% más rápido)
        self.current_speed = self.base_speed
        
        # Estamina
        self.max_stamina = 100.0
        self.stamina = self.max_stamina
        self.stamina_drain_rate = 30.0   # Costo por segundo al esprintar
        self.stamina_regen_rate = 15.0   # Regeneración por segundo
        self.min_stamina_for_sprint = 5.0 # Estamina mínima para iniciar
        
        self._dir = Vector2(0.0, 0.0)
        self._progress = 0.0
        self.accel_time = max(1e-4, accel_time)
        self._velocity = Vector2(0.0, 0.0)

    # --- Static Helper Methods ---
    # These methods must be defined inside the class for Player._length to work.

    @staticmethod
    def _length(v: Vector2) -> float:
        """Calcula la magnitud (longitud) de un vector."""
        return math.hypot(v.x, v.y)

    @staticmethod
    def _normalize(v: Vector2) -> Vector2:
        """Normaliza un vector para que su longitud sea 1."""
        l = Player._length(v)
        if l > 1e-9:
            return Vector2(v.x / l, v.y / l)
        return Vector2(0.0, 0.0)

    @staticmethod
    def _dot(a: Vector2, b: Vector2) -> float:
        """Calcula el producto punto de dos vectores."""
        return a.x * b.x + a.y * b.y

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Función de easing para suavizar la aceleración/desaceleración."""
        if t <= 0.0: return 0.0
        if t >= 1.0: return 1.0
        return t * t * (3.0 - 2.0 * t)

    # -----------------------------

    def update(self, move_axis: Vector2, is_sprinting: bool, dt: float) -> None:
        mag = Player._length(move_axis)
        moving = mag > 1e-6
        
        # --- Lógica de Sprint y Estamina ---
        # Note: can_sprint check (stamina > 0.0) is redundant since min_stamina_for_sprint is checked below.
        
        # El jugador está esprintando si lo intenta, puede hacerlo y se está moviendo.
        is_actually_sprinting = is_sprinting and moving and (self.stamina >= self.min_stamina_for_sprint)
        
        if is_actually_sprinting:
            self.current_speed = self.sprint_speed
            self.stamina = max(0.0, self.stamina - self.stamina_drain_rate * dt)
        else:
            self.current_speed = self.base_speed
            # Regeneración (si no estamos esprintando y no estamos al máximo)
            if self.stamina < self.max_stamina:
                self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen_rate * dt)
        # -----------------------------------

        if moving:
            new_dir = Player._normalize(move_axis)
            
            # Lógica para evitar el tambaleo (basada en la última corrección)
            if Player._length(self._dir) > 1e-6 and Player._dot(new_dir, self._dir) < -0.1:
                self._progress = 0.0
            
            self._dir = new_dir 
            self._progress += dt / self.accel_time
        else:
            self._progress -= dt / self.accel_time

        self._progress = max(0.0, min(1.0, self._progress))
        speed_mult = Player.ease_in_out(self._progress)
        
        # Usar self.current_speed
        vx = self._dir.x * self.current_speed * speed_mult
        vy = self._dir.y * self.current_speed * speed_mult
        self._velocity.x = vx
        self._velocity.y = vy

        self.position.x += vx * dt
        self.position.y += vy * dt

    def draw(self) -> None:
        # Dibuja un simple cuadrado centrado en self.position
        x = int(self.position.x - self.size / 2)
        y = int(self.position.y - self.size / 2)
        draw_rectangle(x, y, self.size, self.size, Color(200, 50, 50, 255))
        
        # Dibujar barra de estamina (ejemplo simple en HUD del jugador)
        bar_w = self.size
        bar_h = 4
        stamina_ratio = self.stamina / self.max_stamina
        
        draw_rectangle(x, y - bar_h - 2, bar_w, bar_h, DARKGRAY)
        draw_rectangle(x, y - bar_h - 2, int(bar_w * stamina_ratio), bar_h, GREEN)