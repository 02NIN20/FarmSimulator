# Code/crop_system.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from pyray import (
    Vector2, Color, BLACK, WHITE, RAYWHITE, GRAY,
    draw_rectangle, draw_rectangle_lines, draw_text, measure_text,
    draw_circle, draw_circle_lines
)

# Semillas permitidas por escena (1..4) usando tu convención de IDs.
# Por defecto las inferimos a partir de lo que ya spawnea cada región.
# Si agregas semillas nuevas en SPAWN_TABLES, se incorporan automáticamente.
from spawn_tables import SPAWN_TABLES  # escena (1..4) -> items{...}  (tú ya lo tienes)

def _allowed_seeds_for_scene(scene_id: int) -> List[str]:
    table = SPAWN_TABLES.get(scene_id, {})
    items = table.get("items", {}) if isinstance(table, dict) else {}
    # Tomamos solo lo que empieza por "seed_"
    return sorted([iid for iid in items.keys() if isinstance(iid, str) and iid.startswith("seed_")])

# Mapa semilla -> producto (para inventario al cosechar).
# Fallback: "seed_xxx" -> "xxx".
SEED_TO_PRODUCT: Dict[str, str] = {
    "seed_wheat": "wheat",
    "seed_spring_wheat": "wheat",
    "seed_barley": "barley",
    "seed_malting_barley": "barley",
    "seed_spring_barley": "barley",
    "seed_sunflower": "sunflower",
    "seed_soy": "soy",
    "seed_potato": "potato",
    "seed_grape": "grape",
    "seed_apple": "apple",
    "seed_carrot": "carrot",
    "seed_blueberry": "blueberry",
    "seed_kale": "kale",
    "seed_corn": "corn",
    "seed_canola": "canola",
    "seed_field_pea": "field_pea",
    "seed_raspberry_ht": "raspberry",
}

def product_from_seed(seed_id: str) -> str:
    if seed_id in SEED_TO_PRODUCT:
        return SEED_TO_PRODUCT[seed_id]
    if seed_id.startswith("seed_") and len(seed_id) > 5:
        return seed_id[5:]
    return seed_id  # último recurso


@dataclass
class CropPlot:
    scene_id: int
    pos: Vector2
    seed_id: str
    label: str
    grow_time: float      # segundos totales para madurar
    progress: float = 0.0 # [0..grow_time]
    ready: bool = False

    def update(self, dt: float) -> None:
        if self.ready:
            return
        self.progress = min(self.grow_time, self.progress + dt)
        if self.progress >= self.grow_time:
            self.ready = True

    def pct(self) -> float:
        if self.grow_time <= 0.0:
            return 1.0
        return max(0.0, min(1.0, self.progress / self.grow_time))


class CropSystem:
    """
    - Mantiene parches por escena.
    - Planta si el inventario tiene la semilla y la semilla es válida para la región.
    - Dibuja etiqueta + barra de progreso sobre el parche.
    - Permite cosechar al estar cerca (devuelve True si cosecha y agrega al inventario).
    """
    def __init__(self) -> None:
        self._plots_by_scene: Dict[int, List[CropPlot]] = {}
        # Balance rápido: tiempos base por tipo (puedes ajustar libremente).
        self._seed_grow_times: Dict[str, float] = {
            "seed_wheat": 60.0, "seed_spring_wheat": 60.0,
            "seed_barley": 65.0, "seed_malting_barley": 70.0, "seed_spring_barley": 65.0,
            "seed_sunflower": 75.0, "seed_soy": 70.0,
            "seed_potato": 80.0, "seed_grape": 95.0, "seed_apple": 110.0,
            "seed_carrot": 55.0, "seed_blueberry": 85.0, "seed_kale": 50.0,
            "seed_corn": 85.0, "seed_canola": 65.0, "seed_field_pea": 60.0,
            "seed_raspberry_ht": 90.0,
        }

    # ----------------- Consulta / reglas -----------------
    def allowed_seeds_here(self, scene_id: int) -> List[str]:
        return _allowed_seeds_for_scene(scene_id)

    def can_plant(self, scene_id: int, seed_id: str) -> bool:
        return seed_id in self.allowed_seeds_here(scene_id)

    # ----------------- Planta -----------------
    def try_plant(self, scene_id: int, world_pos: Vector2, seed_id: str, inventory) -> bool:
        """
        Intenta plantar: valida región + inventario. Consume 1 semilla si procede.
        """
        if not self.can_plant(scene_id, seed_id):
            return False
        # Inventario debe tener la semilla
        try:
            if not inventory.has_item(seed_id, 1):
                return False
        except Exception:
            return False

        # Consumir 1 semilla
        removed = 0
        try:
            removed = inventory.remove_item(seed_id, 1)
        except Exception:
            removed = 0
        if removed <= 0:
            return False

        # Crear parche
        time_needed = self._seed_grow_times.get(seed_id, 60.0)
        label = product_from_seed(seed_id).replace("_", " ").title()
        plot = CropPlot(
            scene_id=scene_id,
            pos=Vector2(float(world_pos.x), float(world_pos.y)),
            seed_id=seed_id,
            label=label,
            grow_time=time_needed,
        )
        self._plots_by_scene.setdefault(scene_id, []).append(plot)
        return True

    # ----------------- Update/draw -----------------
    def update(self, dt: float, scene_id: int) -> None:
        for p in self._plots_by_scene.get(scene_id, []):
            p.update(dt)

    def draw_world(self, scene_id: int) -> None:
        """
        Dibuja el parche (marco simple) + barra + etiqueta encima, en coordenadas de mundo.
        """
        for p in self._plots_by_scene.get(scene_id, []):
            x = int(p.pos.x)
            y = int(p.pos.y)

            # “terreno” visual simple
            draw_circle(x, y, 18, Color(110, 90, 60, 160))
            draw_circle_lines(x, y, 18, Color(40, 30, 20, 200))

            # Barra
            bw, bh = 84, 14
            bx, by = x - bw // 2, y - 32
            # fondo
            draw_rectangle(bx, by, bw, bh, Color(30, 30, 30, 170))
            draw_rectangle_lines(bx, by, bw, bh, Color(15, 15, 15, 220))
            # fill
            inner = int((bw - 6) * p.pct())
            if inner > 0:
                draw_rectangle(bx + 3, by + 3, inner, bh - 6, Color(90, 170, 60, 255))

            # Etiqueta
            fs = 16
            txt = (p.label + (" (Listo)" if p.ready else ""))
            tx = x - measure_text(txt, fs) // 2
            draw_text(txt, tx, by - fs - 6, fs, WHITE if p.ready else RAYWHITE)

    # ----------------- Interacción cosecha -----------------
    def try_harvest_near(self, scene_id: int, player_pos: Vector2, inventory, radius: float = 34.0) -> bool:
        """
        Si hay un cultivo listo cerca, lo recoge y lo agrega al inventario (qty=1 por parche).
        Devuelve True si cosechó algo.
        """
        plist = self._plots_by_scene.get(scene_id, [])
        if not plist:
            return False

        # Buscar el más cercano que esté listo
        nearest_idx = -1
        nearest_d2 = 1e18
        for i, p in enumerate(plist):
            if not p.ready:
                continue
            dx = player_pos.x - p.pos.x
            dy = player_pos.y - p.pos.y
            d2 = dx * dx + dy * dy
            if d2 < radius * radius and d2 < nearest_d2:
                nearest_d2 = d2
                nearest_idx = i

        if nearest_idx < 0:
            return False

        plot = plist[nearest_idx]
        prod = product_from_seed(plot.seed_id)
        # Entrega 1 unidad (puedes balancear cantidades aquí)
        added_ok = False
        try:
            added_ok = inventory.add_item(prod, 1)
        except Exception:
            added_ok = False

        # Si no cupo, no remover el parche (deja que el jugador haga espacio)
        if not added_ok:
            return False

        # Remover el parche cosechado
        plist.pop(nearest_idx)
        return True

    # ----------------- Utilidades -----------------
    def list_plots(self, scene_id: int) -> List[CropPlot]:
        return list(self._plots_by_scene.get(scene_id, []))
