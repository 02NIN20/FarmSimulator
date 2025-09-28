# Collisions.py
"""Mapa de colisiones basado en grid.
   - Cada celda puede marcarse como sólida (True/False).
   - Soporta comprobación de colisión punto/rect/celda y
     export/import de un listado de rectángulos (para almacenar en archivo).
"""

from __future__ import annotations
from typing import Tuple, List, Iterable

class CollisionMap:
    """
    CollisionMap gestiona una rejilla de celdas sólidas.
    Coordenadas internas: (col, row) con 0..cols-1 y 0..rows-1.
    cell_size_x, cell_size_y definen tamaño del tile en píxeles.
    """

    def __init__(self, cols: int, rows: int, cell_size_x: int, cell_size_y: int) -> None:
        self.cols = cols
        self.rows = rows
        self.cell_w = cell_size_x
        self.cell_h = cell_size_y
        # grid booleana (col-major). Inicialmente todo False (no sólido)
        self.grid = [[False for _ in range(rows)] for _ in range(cols)]

        # Alternativa: lista de rects (x,y,w,h) si prefieres rectangulos arbitrarios
        self.rect_colliders: List[Tuple[float, float, float, float]] = []

    # --- Grid cell operations ---
    def in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.cols and 0 <= row < self.rows

    def set_solid(self, col: int, row: int, solid: bool = True) -> None:
        if self.in_bounds(col, row):
            self.grid[col][row] = bool(solid)

    def is_solid(self, col: int, row: int) -> bool:
        if self.in_bounds(col, row):
            return self.grid[col][row]
        return False

    def toggle(self, col: int, row: int) -> None:
        if self.in_bounds(col, row):
            self.grid[col][row] = not self.grid[col][row]

    # --- Rect / point collision queries (in world coordinates, px) ---
    def world_to_cell(self, x: float, y: float) -> Tuple[int, int]:
        """Convierte (x,y) en píxeles a (col,row)."""
        col = int(x // self.cell_w)
        row = int(y // self.cell_h)
        return col, row

    def rect_to_cells(self, x: float, y: float, w: float, h: float) -> Iterable[Tuple[int, int]]:
        """Devuelve todas las celdas tocadas por el rectángulo (x,y,w,h)."""
        left_col, top_row = self.world_to_cell(x, y)
        right_col, bottom_row = self.world_to_cell(x + w - 1e-6, y + h - 1e-6)
        # clamp
        left_col = max(0, left_col); top_row = max(0, top_row)
        right_col = min(self.cols - 1, right_col); bottom_row = min(self.rows - 1, bottom_row)
        for c in range(left_col, right_col + 1):
            for r in range(top_row, bottom_row + 1):
                yield (c, r)

    def rect_collides_grid(self, x: float, y: float, w: float, h: float) -> bool:
        """True si cualquier celda sólida intersecta al rect (x,y,w,h)."""
        for (c, r) in self.rect_to_cells(x, y, w, h):
            if self.grid[c][r]:
                return True
        return False

    # --- Rect colliders independientes (no grid) ---
    def add_rect_collider(self, x: float, y: float, w: float, h: float) -> None:
        self.rect_colliders.append((x, y, w, h))

    def clear_rect_colliders(self) -> None:
        self.rect_colliders.clear()

    def rect_collides_any(self, x: float, y: float, w: float, h: float) -> bool:
        """Comprueba colisión contra rect_colliders y grid-cells."""
        # primero grid
        if self.rect_collides_grid(x, y, w, h):
            return True
        # luego rects arbitrarios (AABB)
        for (rx, ry, rw, rh) in self.rect_colliders:
            if not (x + w <= rx or x >= rx + rw or y + h <= ry or y >= ry + rh):
                return True
        return False

    # --- Export / import (útil para guardar en archivo separado) ---
    def export_solid_cells(self) -> List[Tuple[int, int]]:
        """Devuelve lista de (col,row) sólidas (para guardar)."""
        out = []
        for c in range(self.cols):
            for r in range(self.rows):
                if self.grid[c][r]:
                    out.append((c, r))
        return out

    def import_solid_cells(self, cells: Iterable[Tuple[int, int]]) -> None:
        for c, r in cells:
            if self.in_bounds(c, r):
                self.grid[c][r] = True
