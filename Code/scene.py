# scene.py
from __future__ import annotations
from typing import Dict, Tuple, Optional, List
from pyray import *
from collisions import CollisionMap  # usamos tu CollisionMap para “sólidos” fuera del polígono

Point = Tuple[float, float]

class Scene:
    def __init__(
        self,
        scene_id: int,
        size: Vector2,
        color: Color,
        spawn: Vector2,
        grid_cell_size: int = 64,
        grid_enabled: bool = True,
        polygon_norm: Optional[List[Point]] = None,  # NUEVO: polígono normalizado (0..1)
    ) -> None:
        self.scene_id = scene_id
        self.size = size
        self.color = color
        self.spawn = spawn

        # Grid
        self.grid_cell_size = grid_cell_size
        self.grid_enabled = grid_enabled

        # Tiles/texturas (aseguramos su existencia)
        self._tiles: Dict[Tuple[int, int], Texture] = {}

        # Polígono (en coords mundo) y mapa de colisión
        self.polygon_world: Optional[List[Vector2]] = None
        self.collision_map: Optional[CollisionMap] = None

        if polygon_norm:
            self._build_polygon_and_collisions(polygon_norm)

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

    # --- Conversión mundo↔celda ---
    def world_to_cell(self, pos: Vector2) -> Tuple[int, int]:
        cs = self.grid_cell_size
        return int(pos.x // cs), int(pos.y // cs)

    def cell_to_world(self, cell: Tuple[int, int]) -> Vector2:
        cs = self.grid_cell_size
        return Vector2(cell[0] * cs, cell[1] * cs)

    # ================= POLÍGONO + COLISIONES =================

    def _build_polygon_and_collisions(self, polygon_norm: List[Point]) -> None:
        """Escala el polígono normalizado al tamaño de escena y crea CollisionMap (sólido = fuera del polígono)."""
        # 1) Escalar a mundo con margen
        margin = 0.06
        W, H = float(self.size.x), float(self.size.y)
        sx, sy = (1.0 - 2 * margin) * W, (1.0 - 2 * margin) * H
        ox, oy = margin * W, margin * H
        self.polygon_world = [Vector2(ox + px * sx, oy + py * sy) for (px, py) in polygon_norm]

        # 2) Crear CollisionMap y marcar FUERA como sólido
        cols = max(1, int(W // self.grid_cell_size))
        rows = max(1, int(H // self.grid_cell_size))
        cm = CollisionMap(cols, rows)

        for r in range(rows):
            for c in range(cols):
                cx = (c + 0.5) * self.grid_cell_size
                cy = (r + 0.5) * self.grid_cell_size
                inside = self._point_in_polygon(cx, cy, self.polygon_world)
                cm.set_solid(c, r, not inside)  # sólido = fuera
        self.collision_map = cm

    @staticmethod
    def _point_in_polygon(x: float, y: float, poly: List[Vector2]) -> bool:
        """Ray casting (par-imp). True si (x,y) está dentro del polígono."""
        inside = False
        n = len(poly)
        for i in range(n):
            j = (i - 1) % n
            xi, yi = poly[i].x, poly[i].y
            xj, yj = poly[j].x, poly[j].y
            intersect = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
            if intersect:
                inside = not inside
        return inside

    # ================= DIBUJO =================

    def draw(self) -> None:
        """
        Si hay polígono: dibuja fondo “agua” y luego la masa terrestre (polígono) con borde.
        Si NO hay polígono: mantiene el rectángulo de siempre.
        """
        if self.polygon_world:
            draw_rectangle(0, 0, int(self.size.x), int(self.size.y), Color(180, 210, 230, 255))  # agua/void
            self._draw_filled_polygon(self.polygon_world, self.color)  # “tierra”
            self._draw_polygon_outline(self.polygon_world, Color(40, 40, 40, 220), 2)
        else:
            draw_rectangle(0, 0, int(self.size.x), int(self.size.y), self.color)

        if self.grid_enabled and self.show_grid:
            cs = self.grid_cell_size
            col = Color(255, 255, 255, 30)
            x = 0
            while x <= int(self.size.x):
                draw_line(x, 0, x, int(self.size.y), col)
                x += cs
            y = 0
            while y <= int(self.size.y):
                draw_line(0, y, int(self.size.x), y, col)
                y += cs

    # --- helpers de dibujo de polígono ---
    def _draw_filled_polygon(self, pts: List[Vector2], color_fill: Color) -> None:
        if len(pts) < 3:
            return
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        center = Vector2(cx, cy)
        for i in range(1, len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            draw_triangle(center, a, b, color_fill)

    def _draw_polygon_outline(self, pts: List[Vector2], col: Color, thickness: int = 1) -> None:
        n = len(pts)
        for i in range(n):
            a = pts[i]
            b = pts[(i + 1) % n]
            draw_line_ex(a, b, float(thickness), col)
