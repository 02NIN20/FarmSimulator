# animals.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
from pyray import *

@dataclass
class AnimalSpec:
    name: str
    friendly: bool
    color: Color
    size: int
    max_hp: float
    speed: float
    detect_range: float = 0.0
    attack_range: float = 0.0
    dps: float = 0.0            # daño por golpe (discreto)
    hit_cooldown: float = 0.8   # intervalo entre golpes

class Animal:
    """Entidad animal muy liviana (rectángulo e IA básica)."""
    __slots__ = ("spec","pos","hp","_wander_t","_attack_t","_dir","alive")

    def __init__(self, spec: AnimalSpec, pos: Vector2) -> None:
        self.spec = spec
        self.pos = Vector2(pos.x, pos.y)
        self.hp = spec.max_hp
        self._wander_t = 0.0
        self._attack_t = 0.0
        self._dir = Vector2(0.0, 0.0)
        self.alive = True

    def aabb(self) -> Rectangle:
        s = self.spec.size
        return Rectangle(self.pos.x - s/2, self.pos.y - s/2, s, s)

    def take_damage(self, dmg: float) -> None:
        self.hp -= max(0.0, dmg)
        if self.hp <= 0:
            self.alive = False

    def _wander(self, dt: float) -> None:
        # Cambia de dirección cada cierto tiempo
        self._wander_t -= dt
        if self._wander_t <= 0:
            self._wander_t = 0.8 + get_random_value(0, 120) / 100.0  # 0.8..2.0 s
            self._dir = Vector2((get_random_value(-100,100))/100.0,
                                (get_random_value(-100,100))/100.0)
        sp = self.spec.speed * 0.45
        self.pos.x += self._dir.x * sp * dt
        self.pos.y += self._dir.y * sp * dt

    def _move_towards(self, target: Vector2, dt: float, speed: float) -> None:
        dx = target.x - self.pos.x
        dy = target.y - self.pos.y
        d2 = dx*dx + dy*dy
        if d2 <= 1e-4:
            return
        dist = d2 ** 0.5
        vx, vy = dx / dist, dy / dist
        step = speed * dt
        if step >= dist:
            self.pos.x, self.pos.y = target.x, target.y
        else:
            self.pos.x += vx * step
            self.pos.y += vy * step

    def update(self, dt: float, player_pos: Vector2) -> Tuple[bool, float]:
        """Devuelve (hit_player, damage) si ataca al jugador este frame."""
        if not self.alive:
            return (False, 0.0)

        hit_player = False
        damage = 0.0

        if self.spec.friendly:
            self._wander(dt)
        else:
            dx = player_pos.x - self.pos.x
            dy = player_pos.y - self.pos.y
            dist = (dx*dx + dy*dy) ** 0.5
            if dist <= self.spec.detect_range:
                self._move_towards(player_pos, dt, self.spec.speed)
                if dist <= self.spec.attack_range:
                    self._attack_t -= dt
                    if self._attack_t <= 0.0:
                        hit_player = True
                        damage = max(0.0, self.spec.dps)
                        self._attack_t = max(0.2, self.spec.hit_cooldown)
                else:
                    self._attack_t = 0.0
            else:
                self._wander(dt)

        return (hit_player, damage)

    def draw(self) -> None:
        if not self.alive:
            return
        s = self.spec.size

        # sombra
        draw_ellipse(int(self.pos.x), int(self.pos.y), int(s*0.45), int(s*0.18), Color(0,0,0,50))
        # cuerpo
        draw_rectangle(int(self.pos.x - s/2), int(self.pos.y - s/2), s, s, self.spec.color)
        draw_rectangle_lines(int(self.pos.x - s/2), int(self.pos.y - s/2), s, s, BLACK)

        # barra de vida
        hp_bar_h = 4
        if self.hp < self.spec.max_hp:
            w = s
            h = hp_bar_h
            ratio = max(0.0, min(1.0, self.hp / self.spec.max_hp))
            draw_rectangle(int(self.pos.x - w/2), int(self.pos.y - s/2 - h - 3), w, h, Color(30,30,30,170))
            draw_rectangle(int(self.pos.x - w/2 + 1), int(self.pos.y - s/2 - h - 2), int((w-2)*ratio), h-2, Color(210,70,70,220))

        # === Etiqueta con icono ===
        fs = max(12, int(s * 0.8))
        icon = "🐾" if self.spec.friendly else "⚔️"
        label = f"{icon} {self.spec.name}"
        text_w = measure_text(label, fs)
        pad_x, pad_y = 6, 4
        box_w = text_w + pad_x * 2
        box_h = fs + pad_y * 2

        top_of_body = int(self.pos.y - s/2)
        top_of_hpbar = top_of_body - (hp_bar_h + 6) if self.hp < self.spec.max_hp else top_of_body
        box_x = int(self.pos.x - box_w / 2)
        box_y = top_of_hpbar - box_h - 6

        back = Color(25, 60, 30, 180) if self.spec.friendly else Color(60, 30, 30, 180)
        border = Color(0, 0, 0, 200)
        fg = RAYWHITE

        try:
            draw_rectangle_rounded(Rectangle(box_x, box_y, box_w, box_h), 0.35, 8, back)
            draw_rectangle_rounded_lines(Rectangle(box_x, box_y, box_w, box_h), 0.35, 8, 2, border)
        except Exception:
            draw_rectangle(box_x, box_y, box_w, box_h, back)
            draw_rectangle_lines(box_x, box_y, box_w, box_h, border)

        tx = box_x + (box_w - text_w) // 2
        ty = box_y + (box_h - fs) // 2
        draw_text(label, tx + 1, ty + 1, fs, Color(0,0,0,120))
        draw_text(label, tx, ty, fs, fg)

# Este módulo se importa desde game.py; no lo ejecutes directamente.
if __name__ == "__main__":
    print("[animals.py] Módulo de entidades animales. Ejecuta el juego con game.py.")
