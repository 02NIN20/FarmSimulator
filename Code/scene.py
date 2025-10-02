# scene.py
from __future__ import annotations
from typing import Dict, Tuple, Optional
from pyray import *

class Scene:
    def __init__(self, scene_id: int, size: Vector2, color: Color, spawn: Vector2,
                 grid_cell_size: int = 64, grid_enabled: bool = True) -> None:
        self.scene_id = scene_id
        self.size = size
        self.color = color
        self.spawn = spawn

        # Grid
        self.grid_cell_size = grid_cell_size
        self.grid_enabled = grid_enabled

        # Tiles/texturas (aseguramos su existencia)
        self._tiles: Dict[Tuple[int, int], Texture] = {}  # <- FIX: asegura que exista

        # (Si tienes mapa de colisiones, podrías conservar tu CollisionMap aquí)
        # self.collision_map = CollisionMap(...)

        # Debug flags
        self.show_grid = True

    # --- Limpieza segura ---
    def __del__(self):
        try:
            self._unload_tiles()
        except Exception:
            pass

    def _unload_tiles(self):
        tiles = getattr(self, "_tiles", None)
        if not tiles:
            return
        for tex in tiles.values():
            try:
                unload_texture(tex)
            except Exception:
                pass
        self._tiles.clear()

    # --- Conversión mundo↔celda (si te sirve para colisiones) ---
    def world_to_cell(self, pos: Vector2) -> Tuple[int, int]:
        cs = self.grid_cell_size
        return int(pos.x // cs), int(pos.y // cs)

    def cell_to_world(self, cell: Tuple[int, int]) -> Vector2:
        cs = self.grid_cell_size
        return Vector2(cell[0] * cs, cell[1] * cs)

    # --- Dibujo ---
    def draw(self) -> None:
        # Fondo del mundo
        draw_rectangle(0, 0, int(self.size.x), int(self.size.y), self.color)

        # (Si tuvieras tiles: dibuja aquí con draw_texture_rec/… usando self._tiles)

        # Rejilla opcional
        if self.grid_enabled and self.show_grid:
            cs = self.grid_cell_size
            col = Color(255, 255, 255, 30)
            # verticales
            x = 0
            while x <= int(self.size.x):
                draw_line(x, 0, x, int(self.size.y), col)
                x += cs
            # horizontales
            y = 0
            while y <= int(self.size.y):
                draw_line(0, y, int(self.size.x), y, col)
                y += cs
