# player.py

from __future__ import annotations
import math
from typing import NamedTuple, Dict, Tuple, Optional

import pyray 
from pyray import *

class PlayerInput(NamedTuple):
    move_vector: Vector2
    is_sprinting: bool
    has_destination: bool
    destination_point: Vector2

class Player:

    def __init__(self, start_pos: Vector2, size: int = 32, speed: float = 240.0, accel_time: float = 0.15) -> None:
        self.position = Vector2(start_pos.x, start_pos.y)
        self.size = size
        self.base_speed = speed      
        self.sprint_speed = speed * 2 
        self.current_speed = self.base_speed
        
        # Atributos de Navegación Point-and-Click
        self.destination = Vector2(start_pos.x, start_pos.y)
        self.TOLERANCE = 5.0
        
        # Estamina
        self.max_stamina = 100.0
        self.stamina = self.max_stamina
        self.stamina_drain_rate = 30.0
        self.stamina_regen_rate = 15.0
        self.min_stamina_for_sprint = 5.0
        
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
        if t <= 0.0: return 0.0
        if t >= 1.0: return 1.0
        return t * t * (3.0 - 2.0 * t)

    def update(self, input_data: PlayerInput, dt: float) -> None:
        
        if input_data.has_destination:
            self.destination = input_data.destination_point
            
        distance_to_dest = Player._length(vector2_subtract(self.destination, self.position))
        
        if distance_to_dest > self.TOLERANCE:
            moving = True
            move_axis = Player._normalize(vector2_subtract(self.destination, self.position))
        else:
            moving = False
            move_axis = Vector2(0.0, 0.0)
            self.destination = self.position
        
        is_sprinting_attempt = input_data.is_sprinting
        is_actually_sprinting = is_sprinting_attempt and moving and (self.stamina >= self.min_stamina_for_sprint)
        
        if is_actually_sprinting:
            self.current_speed = self.sprint_speed
            self.stamina = max(0.0, self.stamina - self.stamina_drain_rate * dt)
        else:
            self.current_speed = self.base_speed
            if self.stamina < self.max_stamina:
                self.stamina = min(self.max_stamina, self.stamina + self.stamina_regen_rate * dt)

        if moving:
            new_dir = move_axis
            if Player._length(self._dir) > 1e-6 and Player._dot(new_dir, self._dir) < -0.1:
                self._progress = 0.0
            self._dir = new_dir 
            self._progress += dt / self.accel_time
        else:
            self._progress -= dt / self.accel_time

        self._progress = max(0.0, min(1.0, self._progress))
        speed_mult = Player.ease_in_out(self._progress)
        
        vx = self._dir.x * self.current_speed * speed_mult
        vy = self._dir.y * self.current_speed * speed_mult
        self._velocity.x = vx
        self._velocity.y = vy

        self.position.x += vx * dt
        self.position.y += vy * dt

    def draw(self) -> None:
        x = int(self.position.x - self.size / 2)
        y = int(self.position.y - self.size / 2)
        draw_rectangle(x, y, self.size, self.size, Color(200, 50, 50, 255))
        
        draw_circle_lines(int(self.destination.x), int(self.destination.y), 5, RED)
        
        bar_w = self.size
        bar_h = 4
        stamina_ratio = self.stamina / self.max_stamina
        
        draw_rectangle(x, y - bar_h - 2, bar_w, bar_h, DARKGRAY)
        draw_rectangle(x, y - bar_h - 2, int(bar_w * stamina_ratio), bar_h, GREEN)