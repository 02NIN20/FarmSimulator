# collisions.py

from __future__ import annotations
from typing import Set, Tuple
from pyray import *

class CollisionMap:
    """Mapa de colisiones simple basado en celdas sólidas."""

    def __init__(self, cols: int, rows: int, cell_w: int, cell_h: int) -> None:
        self.cols = cols
        self.rows = rows
        self.cell_w = cell_w
        self.cell_h = cell_h
        # Almacena las coordenadas de las celdas que son sólidas
        self._solid_cells: Set[Tuple[int, int]] = set()

    def set_solid(self, col: int, row: int, solid: bool = True) -> None:
        """Marca una celda como sólida o no sólida."""
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return
        key = (col, row)
        if solid:
            self._solid_cells.add(key)
        elif key in self._solid_cells:
            self._solid_cells.remove(key)

    def is_solid(self, col: int, row: int) -> bool:
        """Verifica si una celda es sólida."""
        if not (0 <= col < self.cols and 0 <= row < self.rows):
            return False
        return (col, row) in self._solid_cells

    def rect_collides_any(self, x: float, y: float, w: float, h: float) -> bool:
        """Verifica si un rectángulo choca con alguna celda sólida."""
        # Se verifica un rango de celdas (optimización)
        start_col = max(0, int(x // self.cell_w))
        end_col = min(self.cols - 1, int((x + w) // self.cell_w))
        start_row = max(0, int(y // self.cell_h))
        end_row = min(self.rows - 1, int((y + h) // self.cell_h))

        for c in range(start_col, end_col + 1):
            for r in range(start_row, end_row + 1):
                if self.is_solid(c, r):
                    # Hay una colisión potencial en esta celda. Para una verificación
                    # más precisa (si el rectángulo realmente solapa la celda),
                    # se necesitaría más lógica, pero para este sistema simple
                    # solo revisamos si la celda es sólida.
                    # Asumiendo que el rect está contenido en el mundo:
                    return True
        return False