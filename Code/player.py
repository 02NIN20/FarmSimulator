# player.py
from __future__ import annotations
from typing import List, Optional, Any
from pyray import *
import os
from math import sqrt

def _paths_variants(filename: str) -> List[str]:
    here = os.path.dirname(__file__)
    cand = [
        os.path.join(here, "assets", filename),
        os.path.join(here, "Assets", filename),
        os.path.join(here, "sprites", filename),
        os.path.join(here, "Sprites", filename),
        os.path.join(here, "characters", filename),
        os.path.join(here, "assets", "characters", filename),
        os.path.join(here, filename),
        os.path.join(here, ".", "assets", filename),
        os.path.join(here, ".", "Sprites", filename),
        os.path.join("assets", filename),
        os.path.join("Assets", filename),
        filename,
    ]
    out, seen = [], set()
    for p in cand:
        pn = os.path.normpath(p)
        if pn not in seen:
            out.append(pn); seen.add(pn)
    return out

def _try_load_texture_many(candidates: List[str]) -> Optional[Texture2D]:
    for p in candidates:
        try:
            if os.path.exists(p):
                return load_texture(p)
        except Exception:
            pass
    return None

class Player:
    def __init__(self, start_pos: Vector2) -> None:
        self.position: Vector2 = Vector2(start_pos.x, start_pos.y)
        self.destination: Vector2 = Vector2(start_pos.x, start_pos.y)
        self.size: float = 24.0

        # Stats
        self.max_hp: float = 100.0
        self.hp: float = 100.0
        self.max_stamina: float = 100.0
        self.stamina: float = 100.0

        # Combate
        self.attack_radius: float = 40.0
        self.attack_damage: float = 22.0
        self.attack_cost_sta: float = 16.0
        self._attack_cd: float = 0.0
        self.attack_cooldown_time: float = 0.45

        # Movimiento / anim
        self.walk_speed: float = 170.0
        self._moving: bool = False
        self._facing_right: bool = True

        self._frames_right: List[Texture2D] = []
        self._frames_left:  List[Texture2D] = []
        self._frame_idle_right: Optional[Texture2D] = None
        self._frame_idle_left:  Optional[Texture2D] = None

        self._visual_height: float = 100
        self._feet_offset: float = 8.0
        self._anim_base_fps: float = 7.0
        self._anim_time: float = 0.0
        self._last_move_dist: float = 0.0

        self._fallback_color = RED
        self._load_sprites()

    def _load_sprites(self) -> None:
        right_files = [
            "DenisseSprites_Caminando_01.png",
            "DenisseSprites_Caminando_02.png",
            "DenisseSprites_Caminando_03.png",
            "DenisseSprites_Caminando_04.png",
        ]
        left_files = [
            "DenisseSprites_Caminando_I05.png",
            "DenisseSprites_Caminando_I06.png",
            "DenisseSprites_Caminando_I07.png",
            "DenisseSprites_Caminando_I08.png",
        ]
        for fn in right_files:
            tex = _try_load_texture_many(_paths_variants(fn))
            if tex: self._frames_right.append(tex)
        for fn in left_files:
            tex = _try_load_texture_many(_paths_variants(fn))
            if tex: self._frames_left.append(tex)

        self._frame_idle_right = self._frames_right[0] if self._frames_right else None
        self._frame_idle_left  = self._frames_left[0]  if self._frames_left  else None

        if not self._frames_right or not self._frames_left:
            print("[PLAYER] Aviso: no se encontraron todos los sprites.")

    def unload(self) -> None:
        for t in self._frames_right:
            try: unload_texture(t)
            except Exception: pass
        for t in self._frames_left:
            try: unload_texture(t)
            except Exception: pass
        self._frames_right.clear()
        self._frames_left.clear()

    @staticmethod
    def _get_attr_or_key(p_input: Any, name: str, default=None):
        try:
            return p_input.get(name)
        except Exception:
            return getattr(p_input, name, default)

    def try_attack(self, dt: float) -> bool:
        """Intenta atacar (controlado desde Game con tecla). Consume STA y respeta cooldown."""
        if self._attack_cd > 0.0:
            return False
        if self.stamina < self.attack_cost_sta:
            return False
        self.stamina = max(0.0, self.stamina - self.attack_cost_sta)
        self._attack_cd = self.attack_cooldown_time
        return True

    def apply_damage(self, dmg: float) -> None:
        self.hp = max(0.0, self.hp - max(0.0, dmg))

    def update(self, p_input: Any, dt: float) -> None:
        # cooldown de ataque
        if self._attack_cd > 0.0:
            self._attack_cd = max(0.0, self._attack_cd - dt)

        # 1) destino
        dest_field = None
        if p_input is not None:
            dest_field = self._get_attr_or_key(p_input, "destination_point", None)
            if dest_field is None:
                dest_field = self._get_attr_or_key(p_input, "destination", None)

        if dest_field is not None:
            if hasattr(dest_field, "x") and hasattr(dest_field, "y"):
                self.destination = Vector2(float(dest_field.x), float(dest_field.y))
            elif isinstance(dest_field, (tuple, list)) and len(dest_field) == 2:
                self.destination = Vector2(float(dest_field[0]), float(dest_field[1]))

        # 2) sprint
        run_flag = False
        if p_input is not None:
            for key in ("is_sprinting","run","running","is_running","sprint","shift"):
                if bool(self._get_attr_or_key(p_input, key, False)):
                    run_flag = True
                    break

        speed = self.walk_speed * 1.20 if (run_flag and self.stamina > 0) else self.walk_speed
        if run_flag and self.stamina > 0:
            self.stamina = max(0.0, self.stamina - 12.0 * dt)
        else:
            self.stamina = min(self.max_stamina, self.stamina + 6.0 * dt)

        # 3) mover hacia destino
        dx = self.destination.x - self.position.x
        dy = self.destination.y - self.position.y
        dist = sqrt(dx*dx + dy*dy)

        moved = False
        moved_dist = 0.0
        if dist > 1.0:
            vx, vy = dx / dist, dy / dist
            step = speed * dt
            if step >= dist:
                self.position.x = self.destination.x
                self.position.y = self.destination.y
                moved_dist = dist
            else:
                self.position.x += vx * step
                self.position.y += vy * step
                moved_dist = step
            moved = True
            if abs(vx) >= 0.1:
                self._facing_right = vx >= 0.0

        # 4) vector directo (por si agregas teclado futuro)
        if (not moved or dist <= 1.0) and p_input is not None:
            mv = self._get_attr_or_key(p_input, "move_vector", None)
            if mv is not None and hasattr(mv, "x") and hasattr(mv, "y"):
                vx, vy = float(mv.x), float(mv.y)
                if abs(vx) > 1e-4 or abs(vy) > 1e-4:
                    step = speed * dt
                    self.position.x += vx * step
                    self.position.y += vy * step
                    moved = True
                    moved_dist = step
                    if abs(vx) >= 0.1:
                        self._facing_right = vx >= 0.0

        self._moving = moved
        self._last_move_dist = moved_dist

        if self._moving:
            current_speed = self._last_move_dist / max(dt, 1e-6)
            factor = max(0.4, min(1.2, current_speed / max(1.0, self.walk_speed)))
            self._anim_time += dt * (self._anim_base_fps / 7.0) * (7.0 * factor)
        else:
            self._anim_time = 0.0

        # clamps
        self.hp = max(0.0, min(self.max_hp, self.hp))
        self.stamina = max(0.0, min(self.max_stamina, self.stamina))

    def draw(self) -> None:
        tex = self._choose_texture()
        if tex is None or getattr(tex, "id", 0) == 0:
            s = int(self.size)
            draw_rectangle(int(self.position.x - s/2), int(self.position.y - s/2), s, s, self._fallback_color)
            draw_rectangle_lines(int(self.position.x - s/2), int(self.position.y - s/2), s, s, BLACK)
            return

        scale = self._visual_height / max(1, tex.height)
        draw_w = int(tex.width * scale)
        draw_h = int(tex.height * scale)
        draw_x = int(self.position.x - draw_w / 2)
        draw_y = int(self.position.y - draw_h + self._feet_offset)

        draw_ellipse(int(self.position.x), int(self.position.y - 1), int(self._visual_height * 0.24), int(self._visual_height * 0.07), Color(0, 0, 0, 58))
        draw_texture_ex(tex, Vector2(draw_x, draw_y), 0.0, scale, WHITE)

    def _choose_texture(self) -> Optional[Texture2D]:
        frames = self._frames_right if self._facing_right else self._frames_left
        idle   = self._frame_idle_right if self._facing_right else self._frame_idle_left
        if not frames:
            return idle
        if not self._moving:
            return idle
        idx = int(self._anim_time) % len(frames)
        return frames[idx]
