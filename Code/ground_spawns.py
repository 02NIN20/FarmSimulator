# ground_spawns.py
from __future__ import annotations
from typing import Dict, List, Tuple, Optional
import random
from pyray import *

# --- Import robusto de SPAWN_TABLES ---
try:
    import spawn_tables as _sp
    SPAWN_TABLES = getattr(_sp, "SPAWN_TABLES", None)
    if not isinstance(SPAWN_TABLES, dict):
        raise ImportError("spawn_tables.SPAWN_TABLES no es un dict o no existe")
except Exception as e:
    print("[ground_spawns] Aviso:", e)
    # Fallback mínimo para no romper el juego si spawn_tables falla o no existe
    SPAWN_TABLES = {
        1: {
            "first_count": (20, 30),
            "repeat_count": (5, 10),
            "items": {
                "leaves":      {"w": 10, "qty": (1, 3)},
                "wood_branch": {"w": 8,  "qty": (1, 2)},
                "rock":        {"w": 6,  "qty": (1, 2)},
            }
        }
    }

class GroundItem:
    __slots__=("item_id","qty","pos","color","size")
    def __init__(self, item_id: str, qty: int, pos: Vector2, color: Color, size: int = 14) -> None:
        self.item_id = item_id
        self.qty = qty
        self.pos = pos
        self.color = color
        self.size = size

class SpawnManager:
    """Spawns persistentes por escena: primera entrada abundante, luego reposición ligera."""
    def __init__(self, inventory) -> None:
        self.inventory = inventory
        self.items_by_scene: Dict[int, List[GroundItem]] = {}
        self.visited: Dict[int, int] = {}  # scene_id -> veces visitada
        self._color_cache: Dict[str, Color] = {}

    # --- API ---
    def on_enter_scene(self, scene_id: int, scene_size: Vector2, polygon: Optional[List[Vector2]] = None) -> None:
        count = self.visited.get(scene_id, 0)
        first_time = count == 0
        self.visited[scene_id] = count + 1

        existing = len(self.items_by_scene.get(scene_id, []))
        target = 0
        tbl = SPAWN_TABLES.get(scene_id, SPAWN_TABLES.get(1, {}))
        first_rng  = tbl.get("first_count",  (20, 30))
        repeat_rng = tbl.get("repeat_count", (5, 10))

        if first_time:
            a, b = first_rng
            target = random.randint(a, b)
        else:
            a, b = repeat_rng
            if existing < a:
                target = random.randint(max(0, a - existing), max(0, b - existing))

        if target > 0:
            batch = self._roll_items(scene_id, target)
            lst = self.items_by_scene.setdefault(scene_id, [])
            for item_id, qty in batch:
                pos = self._random_position(scene_size, polygon)
                color = self._get_color(item_id)
                lst.append(GroundItem(item_id, qty, pos, color))

    def update(self, scene_id: int, player_pos: Vector2, pickup_radius: float = 22.0) -> None:
        arr = self.items_by_scene.get(scene_id, [])
        if not arr:
            return
        # más cercano dentro del radio
        best_i = -1
        best_d2 = pickup_radius * pickup_radius
        for i, gi in enumerate(arr):
            dx = player_pos.x - gi.pos.x
            dy = player_pos.y - gi.pos.y
            d2 = dx*dx + dy*dy
            if d2 <= best_d2:
                best_d2 = d2
                best_i = i
        if best_i >= 0:
            gi = arr[best_i]
            label = f"[E] Recoger {gi.item_id} x{gi.qty}"
            fs = 18
            tw = measure_text(label, fs)
            draw_rectangle(int(gi.pos.x - tw/2) - 6, int(gi.pos.y - 32), tw + 12, fs + 8, Color(0,0,0,150))
            draw_text(label, int(gi.pos.x - tw/2), int(gi.pos.y - 28), fs, Color(255,255,255,240))
            if is_key_pressed(KEY_E):
                self.inventory.add_item(gi.item_id, gi.qty)
                arr.pop(best_i)

    def draw(self, scene_id: int) -> None:
        arr = self.items_by_scene.get(scene_id, [])
        for gi in arr:
            x = int(gi.pos.x - gi.size/2)
            y = int(gi.pos.y - gi.size/2)
            draw_rectangle(x, y, gi.size, gi.size, gi.color)
            draw_rectangle_lines(x, y, gi.size, gi.size, Color(0,0,0,170))

    # --- Internos ---
    def _roll_items(self, scene_id: int, n: int) -> List[Tuple[str,int]]:
        tbl = SPAWN_TABLES.get(scene_id, SPAWN_TABLES.get(1, {}))
        items = tbl.get("items", {})
        if not items:
            return [("leaves", 1) for _ in range(n)]
        pool = [(iid, int(meta.get("w",1)), meta.get("qty",(1,1))) for iid, meta in items.items()]
        total_w = sum(w for _, w, _ in pool) or 1
        out: List[Tuple[str,int]] = []
        for _ in range(n):
            r = random.uniform(0, total_w)
            acc = 0.0
            pick = pool[-1]
            for entry in pool:
                acc += entry[1]
                if r <= acc:
                    pick = entry
                    break
            qmin, qmax = pick[2]
            out.append((pick[0], random.randint(qmin, qmax)))
        return out

    def _get_color(self, item_id: str) -> Color:
        col = self._color_cache.get(item_id)
        if col is not None:
            return col
        try:
            col = self.inventory.item_database[item_id].icon_color
        except Exception:
            col = Color(200,200,200,255)
        self._color_cache[item_id] = col
        return col

    def _random_position(self, scene_size: Vector2, polygon: Optional[List[Vector2]]) -> Vector2:
        pad = 48
        if not polygon:
            return Vector2(random.uniform(pad, scene_size.x - pad),
                           random.uniform(pad, scene_size.y - pad))
        # muestreo por rechazo dentro del polígono (si existe)
        min_x = min(p.x for p in polygon); max_x = max(p.x for p in polygon)
        min_y = min(p.y for p in polygon); max_y = max(p.y for p in polygon)
        for _ in range(50):
            x = random.uniform(min_x + pad, max_x - pad)
            y = random.uniform(min_y + pad, max_y - pad)
            if self._point_in_polygon(x, y, polygon):
                return Vector2(x, y)
        return Vector2(random.uniform(pad, scene_size.x - pad),
                       random.uniform(pad, scene_size.y - pad))

    def _point_in_polygon(self, x: float, y: float, pts: List[Vector2]) -> bool:
        inside = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i].x, pts[i].y
            xj, yj = pts[j].x, pts[j].y
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-9) + xi):
                inside = not inside
            j = i
        return inside
