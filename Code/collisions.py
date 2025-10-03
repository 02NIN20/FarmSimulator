# Code/collisions.py
from __future__ import annotations
from typing import List, Tuple, Optional

# ---------------------------------------------------------------
# CollisionMap retro-compatible:
#   - Antiguo: CollisionMap(cols:int, rows:int)
#   - Nuevo:   CollisionMap(polygon_world: List[(x,y)], scene_w:float, scene_h:float)
# API compatibles con escenas antiguas:
#   - set_solid(col:int, row:int, solid:bool)
#   - rect_collides(x, y, w, h, cell_w, cell_h) -> bool
# ---------------------------------------------------------------

def _point_in_poly(px: float, py: float, poly: List[Tuple[float, float]]) -> bool:
    """Ray casting point-in-polygon."""
    inside = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-9) + xi):
            inside = not inside
        j = i
    return inside


class CollisionMap:
    def __init__(self, a, b=None, c=None) -> None:
        """
        Antiguo: CollisionMap(cols:int, rows:int)
        Nuevo:   CollisionMap(polygon_world: List[(x,y)], scene_w:float, scene_h:float)
        """
        # Datos de rejilla (opcional)
        self.cols: Optional[int] = None
        self.rows: Optional[int] = None
        self.blocked: set[tuple[int, int]] = set()

        # Datos de polígono / mundo (opcional)
        self.poly: Optional[List[Tuple[float, float]]] = None
        self.scene_w: Optional[float] = None
        self.scene_h: Optional[float] = None

        # Detectar firma
        if isinstance(a, int) and isinstance(b, int) and c is None:
            # Firma antigua (cols, rows)
            self.cols = int(a)
            self.rows = int(b)
        else:
            # Firma nueva (polygon_world, scene_w, scene_h)
            self.set_polygon(a, b, c)

    # -------- API polígono --------
    def set_polygon(self, polygon_world: Optional[List[Tuple[float, float]]],
                    scene_w: Optional[float], scene_h: Optional[float]) -> None:
        self.poly = polygon_world
        self.scene_w = float(scene_w) if scene_w is not None else None
        self.scene_h = float(scene_h) if scene_h is not None else None

    # -------- API rejilla (compat.) --------
    def set_solid(self, ix: int, iy: int, solid: bool) -> None:
        """Compatibilidad con escenas antiguas: marca/desmarca celda sólida."""
        if solid:
            self.blocked.add((int(ix), int(iy)))
        else:
            self.blocked.discard((int(ix), int(iy)))

    # Utilidades equivalentes (por si las necesitas en otros lados)
    def block_cell(self, ix: int, iy: int, blocked: bool = True) -> None:
        self.set_solid(ix, iy, blocked)

    def clear_all_blocks(self) -> None:
        self.blocked.clear()

    # -------- Consulta colisión --------
    def rect_collides(self, x: float, y: float, w: float, h: float,
                      cell_w: float, cell_h: float) -> bool:
        """True si el AABB choca con: límites, polígono (si hay) o celdas sólidas."""
        # Tamaño del mundo
        world_w = self.scene_w if self.scene_w is not None else (
            (self.cols or 0) * float(cell_w)
        )
        world_h = self.scene_h if self.scene_h is not None else (
            (self.rows or 0) * float(cell_h)
        )

        # Límites
        if world_w and world_h:
            if x < 0 or y < 0 or (x + w) > world_w or (y + h) > world_h:
                return True

        # Límite por polígono (si existe)
        if self.poly:
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            for cx, cy in corners:
                if not _point_in_poly(cx, cy, self.poly):
                    return True

        # Celdas bloqueadas
        if self.blocked:
            # Si no hay cols/rows pero sí tamaño del mundo, derivarlos
            cols = self.cols if self.cols is not None else (int(world_w // cell_w) if world_w else 0)
            rows = self.rows if self.rows is not None else (int(world_h // cell_h) if world_h else 0)

            ix0 = max(0, int(x // cell_w))
            iy0 = max(0, int(y // cell_h))
            ix1 = min(max(0, cols - 1), int((x + w) // cell_w))
            iy1 = min(max(0, rows - 1), int((y + h) // cell_h))

            for iy in range(iy0, iy1 + 1):
                for ix in range(ix0, ix1 + 1):
                    if (ix, iy) in self.blocked:
                        return True

        return False
