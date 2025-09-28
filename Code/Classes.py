# Classes.py
"""Contiene Player (movement ease in/out) y Scene con grid, tiles y colisiones.
   Scene usa CollisionMap (importado desde collisions.py) para gestionar colisiones por separado.
"""

from __future__ import annotations
import math
from typing import Dict, Tuple, Optional
from pyray import *  # Vector2, load_texture, unload_texture, draw_texture_ex, draw_rectangle_lines, draw_rectangle, Color
from Collisions import CollisionMap

# ---------------------------
# Player (ease in/out)
# ---------------------------
class Player:
    """Jugador con ease-in/out en aceleración (versión simple)."""

    def __init__(self, start_pos: Vector2, size: int = 32, speed: float = 240.0, accel_time: float = 0.15) -> None:
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

        self._progress = max(0.0, min(1.0, self._progress))
        speed_mult = Player.ease_in_out(self._progress)
        vx = self._dir.x * self.speed * speed_mult
        vy = self._dir.y * self.speed * speed_mult
        self._velocity.x = vx
        self._velocity.y = vy

        self.position.x += vx * dt
        self.position.y += vy * dt

    def draw(self) -> None:
        # Dibuja un simple cuadrado centrado en self.position
        x = int(self.position.x - self.size / 2)
        y = int(self.position.y - self.size / 2)
        draw_rectangle(x, y, self.size, self.size, Color(200, 50, 50, 255))

# ---------------------------
# Scene con grid y tiles
# ---------------------------
class Scene:
    """
    Scene con:
      - id, size (Vector2), color de fondo, spawn (Vector2)
      - grid (cols x rows) con cell_w / cell_h (pixeles)
      - ability to set tile textures per cell (stores and dibuja)
      - CollisionMap asociado (por separado: collisions.py)
    """

    def __init__(self, scene_id: int, size: Vector2, color: Color, spawn: Vector2, cell_w: int = 32, cell_h: int = 32) -> None:
        self.id = scene_id
        self.size = Vector2(size.x, size.y)
        self.color = color
        self.spawn = Vector2(spawn.x, spawn.y)

        # grid parameters
        self.cell_w = int(cell_w)
        self.cell_h = int(cell_h)
        self.cols = max(1, int(self.size.x) // self.cell_w)
        self.rows = max(1, int(self.size.y) // self.cell_h)

        # tiles: mapping (col,row) -> Texture2D
        self._tiles: Dict[Tuple[int, int], Texture2D] = {}
        # also store source paths (optional) to allow reload/unload
        self._tile_paths: Dict[Tuple[int, int], str] = {}

        # collision map (from collisions.py)
        self.collision_map = CollisionMap(self.cols, self.rows, self.cell_w, self.cell_h)

        # whether to draw grid lines
        self.show_grid = True
        self.grid_color = Color(120, 120, 120, 120)

    # --- Tile management ---
    def set_tile_from_path(self, col: int, row: int, image_path: str) -> None:
        """Carga una textura desde ruta y la asigna a (col,row)."""
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return
        # unload previous if present
        key = (col, row)
        if key in self._tiles:
            try:
                unload_texture(self._tiles[key])
            except Exception:
                pass
            del self._tiles[key]
            del self._tile_paths[key]
        try:
            tex = load_texture(image_path)
            self._tiles[key] = tex
            self._tile_paths[key] = image_path
        except Exception:
            # fallo al cargar; ignorar o loggear
            print(f"[Scene] Error cargando textura {image_path} para celda {key}")

    def set_tile_texture(self, col: int, row: int, texture: Texture2D) -> None:
        """Asigna una Texture2D ya cargada a una celda (no la unloadea automáticamente)."""
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return
        self._tiles[(col, row)] = texture

    def clear_tile(self, col: int, row: int) -> None:
        key = (col, row)
        if key in self._tiles:
            try:
                unload_texture(self._tiles[key])
            except Exception:
                pass
            del self._tiles[key]
            if key in self._tile_paths:
                del self._tile_paths[key]

    def get_tile(self, col: int, row: int) -> Optional[Texture2D]:
        return self._tiles.get((col, row), None)

    # --- Grid helpers ---
    def cell_to_world(self, col: int, row: int) -> Tuple[int, int]:
        """Devuelve corner superior-izq en píxeles de la celda."""
        return int(col * self.cell_w), int(row * self.cell_h)

    def world_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        return int(x // self.cell_w), int(y // self.cell_h)

    # --- Collision helpers (delegan en collision_map) ---
    def set_solid_cell(self, col: int, row: int, solid: bool = True) -> None:
        self.collision_map.set_solid(col, row, solid)

    def is_solid_cell(self, col: int, row: int) -> bool:
        return self.collision_map.is_solid(col, row)

    def rect_collides(self, x: float, y: float, w: float, h: float) -> bool:
        return self.collision_map.rect_collides_any(x, y, w, h)

    # --- Drawing ---
    def draw(self) -> None:
        """Dibuja fondo, tiles y grid lines."""
        # fondo (scene rectangle)
        draw_rectangle(0, 0, int(self.size.x), int(self.size.y), self.color)

        # tiles
        for (col, row), tex in list(self._tiles.items()):
            if tex is None:
                continue
            wx, wy = self.cell_to_world(col, row)
            # escala para que la textura quepa en la celda
            scale_x = self.cell_w / max(1, tex.width)
            scale_y = self.cell_h / max(1, tex.height)
            # se mantiene aspecto original (fit inside)
            scale = min(scale_x, scale_y)
            draw_texture_ex(tex, Vector2(wx, wy), 0.0, scale, Color(255, 255, 255, 255))

        # grid lines
        if self.show_grid:
            # vertical
            for c in range(self.cols + 1):
                x = c * self.cell_w
                draw_rectangle_lines(x, 0, 1, int(self.size.y), self.grid_color)
            # horizontal
            for r in range(self.rows + 1):
                y = r * self.cell_h
                draw_rectangle_lines(0, y, int(self.size.x), 1, self.grid_color)

        # (optional) draw colliders overlay — useful for debugging
        # dibujar celdas sólidas en otro color con alpha
        for c in range(self.cols):
            for r in range(self.rows):
                if self.collision_map.is_solid(c, r):
                    wx, wy = self.cell_to_world(c, r)
                    draw_rectangle(wx, wy, self.cell_w, self.cell_h, Color(200, 40, 40, 90))
