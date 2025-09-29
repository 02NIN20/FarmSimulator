# entities.py

from __future__ import annotations
import math
from typing import Dict, Tuple, Optional
from pyray import *
from collisions import CollisionMap

class Scene:
    """Contenedor para el mundo de juego (fondo, grid, tiles y mapa de colisiones)."""

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
        self._tile_paths: Dict[Tuple[int, int], str] = {} # paths solo si se cargan desde archivo

        # collision map
        self.collision_map = CollisionMap(self.cols, self.rows, self.cell_w, self.cell_h)

        self.show_grid = True
        self.grid_color = Color(120, 120, 120, 120)
        
    def __del__(self) -> None:
        """Limpieza de texturas al destruir la escena."""
        self._unload_tiles()

    def _unload_tiles(self) -> None:
        """Descarga todas las texturas cargadas por la escena."""
        for tex in self._tiles.values():
            try:
                unload_texture(tex)
            except Exception:
                pass
        self._tiles.clear()
        self._tile_paths.clear()

    # --- Tile management ---
    def set_tile_from_path(self, col: int, row: int, image_path: str) -> None:
        """Carga una textura desde ruta y la asigna a (col,row)."""
        if not (0 <= col < self.cols and 0 <= row < self.rows): return
        
        key = (col, row)
        # Descargar la anterior si existía
        if key in self._tiles:
            try: unload_texture(self._tiles[key])
            except Exception: pass
            del self._tiles[key]
            if key in self._tile_paths: del self._tile_paths[key]
            
        try:
            tex = load_texture(image_path)
            self._tiles[key] = tex
            self._tile_paths[key] = image_path
        except Exception:
            print(f"[Scene] Error cargando textura {image_path} para celda {key}")

    # (Métodos set_tile_texture, clear_tile, get_tile, cell_to_world, world_to_cell, set_solid_cell, is_solid_cell, rect_collides_any se mantienen igual o con ligeros ajustes de type hints)

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
            if tex is None: continue
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
        for c in range(self.cols):
            for r in range(self.rows):
                if self.collision_map.is_solid(c, r):
                    wx, wy = self.cell_to_world(c, r)
                    draw_rectangle(wx, wy, self.cell_w, self.cell_h, Color(200, 40, 40, 90))