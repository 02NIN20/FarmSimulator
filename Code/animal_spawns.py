# Code/animal_spawns.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
from math import sqrt, copysign
from random import uniform, randint, choice

from pyray import (
    Vector2, Color, draw_circle, draw_circle_lines, draw_text, measure_text,
    draw_texture_ex, WHITE
)

# Importa el módulo base con specs + sprites
import animals as AM  # AM.SPECS, AM.get_textures_for, AM.register_species_sprites

# ============================================================
# Entidad Animal (instancia en el mundo)
# ============================================================

class AnimalEntity:
    def __init__(self, species: str, position: Vector2) -> None:
        self.species = species
        spec = AM.SPECS.get(species)
        if spec is None:
            # fallback minimal
            spec = AM.AnimalSpec(species, 60.0, 60.0, 0.0, 0.0, 30.0, size=32.0)

        self.spec = spec
        self.pos = Vector2(position.x, position.y)
        self.vel = Vector2(0.0, 0.0)
        self.hp = spec.hp
        self.alive = True

        # Dirección mirando (True => derecha, False => izquierda)
        self.face_right = True

        # Wander: objetivo temporal
        self._wander_target = Vector2(self.pos.x + uniform(-80, 80), self.pos.y + uniform(-80, 80))
        self._wander_timer = uniform(0.8, 2.2)

        # Ataque/daño cadenciado
        self._damage_cooldown = 0.0  # seg. hasta poder hacer daño de nuevo

    def is_aggressive(self) -> bool:
        return self.spec.aggro_radius > 0.0 and self.spec.damage > 0.0

    def _dist2(self, p: Vector2) -> float:
        dx = self.pos.x - p.x
        dy = self.pos.y - p.y
        return dx*dx + dy*dy

    def _norm(self, v: Vector2) -> Vector2:
        mag = sqrt(v.x*v.x + v.y*v.y)
        if mag <= 1e-6:
            return Vector2(0.0, 0.0)
        return Vector2(v.x/mag, v.y/mag)

    def update(self, dt: float, player_pos: Vector2, scene_size: Vector2) -> float:
        """
        Actualiza el animal y devuelve daño hecho al jugador este frame (0 si nada).
        """
        if not self.alive:
            return 0.0

        # Reducir cooldown de daño
        if self._damage_cooldown > 0.0:
            self._damage_cooldown = max(0.0, self._damage_cooldown - dt)

        damage_to_player = 0.0

        # Comportamiento: agresivo o vagar
        if self.is_aggressive() and self._dist2(player_pos) <= (self.spec.aggro_radius ** 2):
            # Perseguir al jugador
            dirv = self._norm(Vector2(player_pos.x - self.pos.x, player_pos.y - self.pos.y))
            self.vel = Vector2(dirv.x * self.spec.speed, dirv.y * self.spec.speed)
            self.face_right = (self.vel.x >= 0.0)

            # Si tocamos al jugador, aplicar daño cadenciado (cada ~0.6s)
            touch_radius = self.spec.size * 0.6
            if self._dist2(player_pos) <= (touch_radius ** 2) and self._damage_cooldown <= 0.0:
                damage_to_player = self.spec.damage
                self._damage_cooldown = 0.6  # 600 ms entre golpes
        else:
            # Vagar: elegir blanco cada cierto tiempo
            self._wander_timer -= dt
            if self._wander_timer <= 0.0 or self._dist2(self._wander_target) < 25**2:
                self._wander_target = Vector2(
                    self.pos.x + uniform(-140, 140),
                    self.pos.y + uniform(-140, 140)
                )
                self._wander_timer = uniform(1.2, 2.6)

            dirw = self._norm(Vector2(self._wander_target.x - self.pos.x,
                                      self._wander_target.y - self.pos.y))
            self.vel = Vector2(dirw.x * self.spec.wander_speed, dirw.y * self.spec.wander_speed)
            self.face_right = (self.vel.x >= 0.0)

        # Integración simple
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        # Limitar a la escena
        self.pos.x = max(0.0, min(scene_size.x, self.pos.x))
        self.pos.y = max(0.0, min(scene_size.y, self.pos.y))

        return damage_to_player

    def apply_damage(self, dmg: float) -> None:
        if dmg <= 0.0 or not self.alive:
            return
        self.hp -= dmg
        if self.hp <= 0.0:
            self.alive = False

    def draw(self) -> None:
        if not self.alive:
            return

        # Intentar sprite; si no hay, dibujar fallback geométrico
        texs = AM.get_textures_for(self.spec.name)
        tex = texs["right"] if self.face_right else texs["left"]

        if tex:
            # Escalamos para que el alto del sprite ≈ self.spec.size
            scale = self.spec.size / max(1.0, float(tex.height))
            draw_texture_ex(tex, Vector2(self.pos.x - (tex.width*scale)/2, self.pos.y - (tex.height*scale)/2),
                            0.0, scale, WHITE)
            return

        # Fallback: círculo con contorno
        base_color = {
            "cow":  Color(230, 230, 230, 255),
            "pig":  Color(255, 180, 180, 255),
            "wolf": Color(150, 160, 170, 255),
            "duck": Color(250, 240, 180, 255),
        }.get(self.spec.name, Color(200, 200, 200, 255))

        r = max(6, int(self.spec.size * 0.5))
        draw_circle(int(self.pos.x), int(self.pos.y), r, base_color)
        draw_circle_lines(int(self.pos.x), int(self.pos.y), r, Color(30, 30, 30, 220))

# ============================================================
# Gestor de animales por escena
# ============================================================

class AnimalManager:
    """
    Mantiene listas de animales por escena y controla spawn/update/draw.
    """
    def __init__(self) -> None:
        # Mapa de escena (0-based dentro del manager) a lista de entidades
        self._by_scene: Dict[int, List[AnimalEntity]] = {}

        # Especies “permitidas para spawnear” (no eliminamos otras de SPECS: solo no las usamos)
        self.allowed_species = ["cow", "pig", "wolf", "duck"]

        # Spawn base por escena (puedes ajustar)
        self.spawn_count_per_scene = {
            0: 0,  # escena 1 local (si no quieres animales ahí)
            1: 6,  # escena 2
            2: 6,  # escena 3
            3: 6,  # escena 4
        }

        # Tamaño de escena (rellenado en on_enter_scene)
        self._last_scene_size: Dict[int, Vector2] = {}

    # -------- Integración con sprites: llamado desde game.py --------
    def set_textures_paths(self, mapping: dict) -> None:
        """
        Recibe dict de rutas por especie y lo registra en animals.py
        (no cargamos texturas aquí; se cargan bajo demanda en draw()).
        """
        try:
            AM.register_species_sprites(mapping)
        except Exception:
            pass  # no romper si algo va mal

    # -------- Hooks desde game.py --------
    def on_enter_scene(self, scene_index: int, scene_size: Vector2, polygon_world=None) -> None:
        """
        Llamado al entrar a una escena (0-based desde game.py).
        Spawnea solo especies permitidas. No borra especies de AM.SPECS.
        """
        self._last_scene_size[scene_index] = scene_size

        if scene_index not in self._by_scene:
            self._by_scene[scene_index] = []

        # Si ya hay animales en esa escena, mantenlos (no “borramos”).
        # Si quieres regenerar, descomenta la siguiente línea:
        # self._by_scene[scene_index].clear()

        need = self.spawn_count_per_scene.get(scene_index, 0)
        # Contar vivos actuales
        alive_now = sum(1 for a in self._by_scene[scene_index] if a.alive)
        to_add = max(0, need - alive_now)

        for _ in range(to_add):
            sp = choice(self.allowed_species)
            x = uniform(scene_size.x * 0.15, scene_size.x * 0.85)
            y = uniform(scene_size.y * 0.15, scene_size.y * 0.85)
            self._by_scene[scene_index].append(AnimalEntity(sp, Vector2(x, y)))

    def update(self, scene_index: int, dt: float, player_pos: Vector2) -> List[float]:
        """
        Actualiza animales de la escena y devuelve lista de daños al jugador este frame.
        """
        damages: List[float] = []
        entities = self._by_scene.get(scene_index, [])
        scene_size = self._last_scene_size.get(scene_index, Vector2(5000.0, 5000.0))

        for a in entities:
            if not a.alive:
                continue
            dmg = a.update(dt, player_pos, scene_size)
            if dmg > 0.0:
                damages.append(dmg)

        # Compactar muertos (si quieres que desaparezcan)
        self._by_scene[scene_index] = [a for a in entities if a.alive]

        return damages

    def draw(self, scene_index: int) -> None:
        """
        Dibuja animales de la escena.
        """
        for a in self._by_scene.get(scene_index, []):
            a.draw()

    def damage_in_radius(self, scene_index: int, pos: Vector2, radius: float, damage: float) -> None:
        """
        Aplica daño a todos los animales en un radio (usado por el ataque del jugador).
        """
        r2 = float(radius) * float(radius)
        for a in self._by_scene.get(scene_index, []):
            if not a.alive:
                continue
            dx = a.pos.x - pos.x
            dy = a.pos.y - pos.y
            if (dx*dx + dy*dy) <= r2:
                a.apply_damage(damage)
