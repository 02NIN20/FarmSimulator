# ground_spawns.py
from __future__ import annotations
from typing import Dict, List
from dataclasses import dataclass
from pyray import (
    Vector2, Color, WHITE, BLACK,
    draw_circle, draw_circle_lines, draw_text, measure_text,
    get_random_value, load_texture, unload_texture, draw_texture_ex
)

# ------------------------------------------------------------
# Parámetros ajustables
# ------------------------------------------------------------
SEED_ICON_SCALE = 0.10        # escala del PNG de semilla (↓ era muy grande)
PICKUP_RADIUS   = 42.0        # radio para auto-pickup
SHOW_DEBUG_ID   = False       # para ver el id encima

@dataclass
class GroundItem:
    item_id: str
    qty: int
    pos: Vector2


class SpawnManager:
    """
    Administra ítems en el suelo.
    Usado por game.py:
      - SpawnManager(inventory)
      - on_enter_scene(scene_index, scene_size, polygon_world)
      - update(scene_index, player_position)
      - draw(scene_index)

    Novedad: texturas de semillas y auto-pickup por proximidad.
    """

    def __init__(self, inventory) -> None:
        self.inventory = inventory
        self._spawns: Dict[int, List[GroundItem]] = {}

        # Texturas
        self._seed_textures: Dict[str, "Texture2D"] = {}
        self._seed_tex_missing: "Texture2D | None" = None

    # ---------------- Texturas ----------------

    def set_seed_textures(self, mapping: Dict[str, str]) -> None:
        """Registra texturas {'seed_wheat': 'assets/trigo_semilla.png', ...}"""
        self.unload_textures()
        for item_id, path in (mapping or {}).items():
            if not path:
                continue
            try:
                tex = load_texture(path)
                self._seed_textures[item_id] = tex
            except Exception:
                pass
        self._seed_tex_missing = None

    def unload_textures(self) -> None:
        for tex in list(self._seed_textures.values()):
            try:
                unload_texture(tex)
            except Exception:
                pass
        self._seed_textures.clear()

        if self._seed_tex_missing is not None:
            try:
                unload_texture(self._seed_tex_missing)
            except Exception:
                pass
        self._seed_tex_missing = None

    def _get_seed_texture(self, item_id: str):
        return self._seed_textures.get(item_id, self._seed_tex_missing)

    # --------------- Ciclo de vida por escena ---------------

    def on_enter_scene(self, scene_index: int, scene_size: Vector2, polygon_world=None) -> None:
        # Si no hay spawns generados para esta escena, generar algunos de ejemplo
        if scene_index not in self._spawns:
            self._spawns[scene_index] = self._quick_generate(scene_size)

    def update(self, scene_index: int, player_pos: Vector2) -> None:
        # Auto-pickup por proximidad
        self._try_auto_pickup(scene_index, player_pos, PICKUP_RADIUS)

    def draw(self, scene_index: int) -> None:
        for g in self._spawns.get(scene_index, []):
            self._draw_ground_item(g)

    # --------------- Generación rápida (demo) ---------------

    def _quick_generate(self, scene_size: Vector2) -> List[GroundItem]:
        out: List[GroundItem] = []
        w, h = float(scene_size.x), float(scene_size.y)

        candidates = [
            "seed_wheat", "seed_barley", "seed_sunflower", "seed_soy",
            "seed_potato", "seed_grape", "seed_apple", "seed_carrot",
            "seed_blueberry", "seed_kale",
        ]

        base_n = 6
        for _ in range(base_n):
            item_id = candidates[get_random_value(0, len(candidates) - 1)]
            qty = get_random_value(1, 2)  # cantidades pequeñas
            x = float(get_random_value(int(w * 0.18), int(w * 0.82)))
            y = float(get_random_value(int(h * 0.18), int(h * 0.82)))
            out.append(GroundItem(item_id=item_id, qty=qty, pos=Vector2(x, y)))
        return out

    # ---------------- Dibujo ----------------

    def _draw_ground_item(self, g: GroundItem) -> None:
        pos = g.pos
        qty = max(1, int(g.qty))
        tex = self._get_seed_texture(g.item_id)

        if tex is not None and getattr(tex, "id", 0) != 0:
            scale = SEED_ICON_SCALE
            draw_w = int(tex.width * scale)
            draw_h = int(tex.height * scale)
            draw_texture_ex(tex, Vector2(pos.x - draw_w / 2, pos.y - draw_h / 2), 0.0, scale, WHITE)
        else:
            # Fallback
            draw_circle(int(pos.x), int(pos.y), 16, Color(60, 60, 60, 70))
            draw_circle_lines(int(pos.x), int(pos.y), 16, Color(30, 30, 30, 90))

        # Cantidad visible
        fs = 16
        label = f"x{qty}"
        draw_text(label, int(pos.x) - measure_text(label, fs) // 2, int(pos.y) - 24, fs, WHITE)

        # Debug opcional del id
        if SHOW_DEBUG_ID:
            dfs = 12
            txt = g.item_id
            draw_text(txt, int(pos.x) - measure_text(txt, dfs) // 2, int(pos.y) - 44, dfs, BLACK)

    # --------------- Auto-pickup ----------------

    def _try_auto_pickup(self, scene_index: int, player_pos: Vector2, radius: float) -> None:
        items = self._spawns.get(scene_index, [])
        if not items:
            return

        keep: List[GroundItem] = []
        r2 = radius * radius

        for g in items:
            dx = player_pos.x - g.pos.x
            dy = player_pos.y - g.pos.y
            if (dx * dx + dy * dy) <= r2:
                # Añadir al inventario
                try:
                    self.inventory.add_item(g.item_id, g.qty)
                except Exception:
                    # Si algo falla, no lo borres
                    keep.append(g)
            else:
                keep.append(g)

        self._spawns[scene_index] = keep
