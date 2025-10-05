
# missions_system.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any

# -----------------------------
# Tipos de objetivos
# -----------------------------

@dataclass
class Objective:
    """Objetivo genérico: se evalúa con `check(context)` y expone progreso (cur, max)."""
    kind: str
    # Para collect: target_id, required_qty
    # Para travel:  scene_ids (set/list), required_visits
    # Para sleep:   required_count
    # Para open_ui: flag_name a marcar cuando se abra
    params: Dict[str, Any]
    title: str

    def progress(self, ctx: "MissionContext") -> Tuple[int, int]:
        k = self.kind
        p = self.params
        if k == "collect":
            item = p["target_id"]
            need = int(p.get("required_qty", 1))
            have = int(ctx.count_item(item))
            return min(have, need), need
        elif k == "travel":
            ids = set(int(x) for x in p.get("scene_ids", []))
            need = int(p.get("required_visits", len(ids)))
            visited = len(ids.intersection(ctx.visited_scenes))
            return min(visited, need), need
        elif k == "sleep":
            need = int(p.get("required_count", 1))
            cur = int(ctx.slept_count)
            return min(cur, need), need
        elif k == "open_ui":
            flag = str(p.get("flag", "opened_missions"))
            cur = 1 if ctx.flags.get(flag, False) else 0
            need = 1
            return cur, need
        else:
            return 0, 1

    def is_done(self, ctx: "MissionContext") -> bool:
        cur, need = self.progress(ctx)
        return cur >= need


@dataclass
class Reward:
    item_id: str
    qty: int


@dataclass
class Mission:
    mission_id: str
    title: str
    lore: str
    objectives: List[Objective] = field(default_factory=list)
    rewards: List[Reward] = field(default_factory=list)
    # runtime
    completed: bool = False
    claimed: bool = False

    def update_state(self, ctx: "MissionContext") -> None:
        self.completed = all(obj.is_done(ctx) for obj in self.objectives)


# -----------------------------
# Contexto inmutable por frame
# -----------------------------

class MissionContext:
    def __init__(self, inventory, visited_scenes: set[int], slept_count: int, flags: Dict[str, bool]):
        self._inv = inventory
        self.visited_scenes = set(visited_scenes)
        self.slept_count = int(slept_count)
        self.flags = dict(flags)

    def count_item(self, item_id: str) -> int:
        try:
            return int(self._inv.count_item(item_id))
        except Exception:
            return 0


# -----------------------------
# Sistema de Misiones
# -----------------------------

class MissionSystem:
    """
    - Lógica y estado de misiones/recompensas (sin UI).
    - UI se dibuja desde game.py utilizando estos datos.
    """
    def __init__(self, inventory) -> None:
        self.inventory = inventory
        self.is_open: bool = False
        self.visited_scenes: set[int] = {1}  # arrancas en Escena 1
        self.slept_count: int = 0
        self.flags: Dict[str, bool] = {"opened_missions": False}

        self.missions: List[Mission] = self._build_campaign()
        self.selected_index: int = 0

    # ---- Campaña (capítulos + mini-misiones) ----
    def _build_campaign(self) -> List[Mission]:
        M: List[Mission] = []

        # ======== HISTORIA PRINCIPAL ========

        # 0) Prólogo: Reentrada
        M.append(Mission(
            "prologue_return",
            "Prólogo — Reentrada",
            ("Denisse fue elegida para regresar a la Tierra. Tu primera tarea es orientarte,\n"
             "revisar tu diario de misiones y reportar señales de supervivencia."),
            objectives=[
                Objective("open_ui", {"flag": "opened_missions"}, "Abre el Diario de Misiones (L)"),
                Objective("travel", {"scene_ids": [1], "required_visits": 1}, "Toca tierra en la Zona Local"),
            ],
            rewards=[Reward("water", 15), Reward("seed_wheat", 4)]
        ))

        # 1) Primeros pasos
        M.append(Mission(
            "first_steps",
            "Cap. 1 — Primeros pasos",
            ("Recolecta recursos cercanos para armar herramientas improvisadas. "
             "Una cuerda te abrirá opciones para fabricar más."),
            objectives=[
                Objective("collect", {"target_id": "wood_branch", "required_qty": 6}, "Reúne 6 Ramas de Madera"),
                Objective("collect", {"target_id": "leaves", "required_qty": 12}, "Reúne 12 Hojas"),
                Objective("collect", {"target_id": "rope", "required_qty": 1}, "Fabrica 1 Cuerda (Mesa de trabajo)"),
            ],
            rewards=[Reward("hoe_wood_improv", 1), Reward("rope_fiber", 2)]
        ))

        # 2) Campamento básico
        M.append(Mission(
            "base_camp",
            "Cap. 2 — Campamento básico",
            ("Para sobrevivir, necesitas un punto seguro. Descansa bajo techo y arma una cama."),
            objectives=[
                Objective("collect", {"target_id": "bed", "required_qty": 1}, "Craftea 1 Cama"),
                Objective("sleep", {"required_count": 1}, "Duerme en una cabaña para guardar"),
            ],
            rewards=[Reward("planks", 6), Reward("seed_corn", 6), Reward("water", 10)]
        ))

        # 3) Reconocimiento del terreno
        M.append(Mission(
            "survey_regions",
            "Cap. 3 — Reconocimiento",
            ("Evalúa la habitabilidad recorriendo distintas ecorregiones. "
             "Visita al menos dos regiones fuera de la Zona Local."),
            objectives=[
                Objective("travel", {"scene_ids": [2, 3, 4], "required_visits": 2}, "Visita 2 regiones distintas (Alaska / PPR / Michigan)"),
            ],
            rewards=[Reward("glass", 2), Reward("jar_small", 1)]
        ))

        # 4) Producción básica
        M.append(Mission(
            "basic_production",
            "Cap. 4 — Producción básica",
            ("Investiga procesos de transformación. El vidrio te permitirá almacenar y analizar muestras."),
            objectives=[
                Objective("collect", {"target_id": "glass", "required_qty": 2}, "Funde 2 de Vidrio en el Horno"),
                Objective("collect", {"target_id": "jar_small", "required_qty": 1}, "Craftea 1 Frasco Pequeño"),
            ],
            rewards=[Reward("water", 30), Reward("seed_wheat", 6)]
        ))

        # 5) Informe inicial
        M.append(Mission(
            "first_report",
            "Cap. 5 — Informe inicial",
            ("Demuestra potencial agrícola consiguiendo un pequeño banco de semillas."),
            objectives=[
                Objective("collect", {"target_id": "VAR_SEEDS_6", "required_qty": 6}, "Reúne 6 tipos de semillas distintos"),
            ],
            rewards=[Reward("fertilizer", 8), Reward("basket", 1)]
        ))

        # ======== MINI-MISIONES (al menos 16) ========

        mini = [
            # Recolección base
            ("mini_leaves", "M1 — Hojas útiles",
             "Recolecta hojas para cuerdas, camas y combustible.",
             [Objective("collect", {"target_id": "leaves", "required_qty": 20}, "Reúne 20 Hojas")],
             [Reward("rope_fiber", 2), Reward("water", 5)]),

            ("mini_branches", "M2 — Ramas para herramientas",
             "Un kit básico empieza con buenas ramas.",
             [Objective("collect", {"target_id": "wood_branch", "required_qty": 12}, "Reúne 12 Ramas de Madera")],
             [Reward("planks", 2)]),

            ("mini_rocks", "M3 — Rocas y minerales",
             "Junta rocas para prototipos de herramientas de piedra.",
             [Objective("collect", {"target_id": "rock", "required_qty": 8}, "Reúne 8 Rocas")],
             [Reward("knife_stone", 1)]),

            ("mini_logs", "M4 — Troncos de reserva",
             "Más tablas, más estructuras. Reúne troncos.",
             [Objective("collect", {"target_id": "log", "required_qty": 2}, "Consigue 2 Troncos")],
             [Reward("planks", 6)]),

            ("mini_rope", "M5 — Soga artesanal",
             "Haz cuerdas con hojas para desbloquear recetas.",
             [Objective("collect", {"target_id": "rope", "required_qty": 2}, "Fabrica 2 Cuerdas")],
             [Reward("stake_wood", 4)]),

            # Herramientas
            ("mini_hoe", "M6 — Azadón improvisado",
             "Un azadón sencillo te prepara para el suelo.",
             [Objective("collect", {"target_id": "hoe_wood_improv", "required_qty": 1}, "Craftea 1 Azadón improvisado")],
             [Reward("fertilizer", 4)]),

            ("mini_pick", "M7 — Pico improvisado",
             "Un pico te permitirá avanzar con minerales.",
             [Objective("collect", {"target_id": "pick_wood_improv", "required_qty": 1}, "Craftea 1 Pico improvisado")],
             [Reward("ore_copper", 2)]),

            ("mini_shovel", "M8 — Pala básica",
             "Una pala completa tu set de herramientas inicial.",
             [Objective("collect", {"target_id": "shovel_wood", "required_qty": 1}, "Craftea 1 Pala de Madera")],
             [Reward("clay", 3)]),

            ("mini_knife", "M9 — Navaja artesanal",
             "Corta y procesa con una herramienta simple.",
             [Objective("collect", {"target_id": "knife_wood", "required_qty": 1}, "Craftea 1 Cuchillo de Madera")],
             [Reward("rope", 1)]),

            # Producción / Horno
            ("mini_glass", "M10 — Vidrio base",
             "Prueba fundir arcilla para obtener vidrio.",
             [Objective("collect", {"target_id": "glass", "required_qty": 1}, "Funde 1 Vidrio")],
             [Reward("glass", 1), Reward("jar_small", 1)]),

            ("mini_copper", "M11 — Cobre refinado",
             "Refina cobre para ampliar herramientas.",
             [Objective("collect", {"target_id": "copper_ingot", "required_qty": 1}, "Funde 1 Lingote de Cobre")],
             [Reward("ore_copper", 2)]),

            ("mini_iron", "M12 — Hierro refinado",
             "Refina hierro para estructuras resistentes.",
             [Objective("collect", {"target_id": "iron_ingot", "required_qty": 1}, "Funde 1 Lingote de Hierro")],
             [Reward("ore_iron", 2)]),

            # Construcción y estaciones
            ("mini_workbench", "M13 — Mesa de trabajo",
             "Tener una mesa de trabajo te acelera el progreso.",
             [Objective("collect", {"target_id": "workbench", "required_qty": 1}, "Craftea 1 Mesa de Trabajo")],
             [Reward("rope", 1), Reward("planks", 4)]),

            ("mini_chest", "M14 — Cofre de madera",
             "Almacena recursos para expediciones largas.",
             [Objective("collect", {"target_id": "chest_wood", "required_qty": 1}, "Craftea 1 Cofre de Madera")],
             [Reward("planks", 4)]),

            ("mini_candles", "M15 — Iluminación",
             "La noche es menos hostil con luz.",
             [Objective("collect", {"target_id": "candle", "required_qty": 2}, "Craftea 2 Velas")],
             [Reward("water", 10)]),

            ("mini_fert", "M16 — Mejorar suelo",
             "Prepara el terreno con enmiendas básicas.",
             [Objective("collect", {"target_id": "bone_meal", "required_qty": 2}, "Craftea 2 Hueso molido")],
             [Reward("fertilizer", 6)]),

            # Exploración específica
            ("mini_visit_alaska", "M17 — Visita: Alaska",
             "Explora la zona boreal para muestras frías.",
             [Objective("travel", {"scene_ids": [2], "required_visits": 1}, "Visita Alaska (Escena 2)")],
             [Reward("seed_potato", 2)]),

            ("mini_visit_ppr", "M18 — Visita: PPR",
             "Explora la pradera para cultivos de grano.",
             [Objective("travel", {"scene_ids": [3], "required_visits": 1}, "Visita PPR (Escena 3)")],
             [Reward("seed_canola", 2)]),

            ("mini_visit_mich", "M19 — Visita: Michigan",
             "Explora la región templada para frutas.",
             [Objective("travel", {"scene_ids": [4], "required_visits": 1}, "Visita Michigan (Escena 4)")],
             [Reward("seed_blueberry", 2)]),

            # Semillas y variedad
            ("mini_jars", "M20 — Frascos de muestra",
             "Prepara contenedores para análisis de suelo y agua.",
             [Objective("collect", {"target_id": "jar_small", "required_qty": 2}, "Craftea 2 Frascos Pequeños")],
             [Reward("water", 10)]),

            ("mini_seeds_var4", "M21 — Mini-banco de semillas",
             "Comienza tu banco de semillas con diversidad mínima.",
             [Objective("collect", {"target_id": "VAR_SEEDS_6", "required_qty": 4}, "Ten al menos 4 tipos distintos de semillas")],
             [Reward("fertilizer", 4)]),

            ("mini_basket", "M22 — Transporte manual",
             "Una cesta ayuda a llevar recursos y cosechas.",
             [Objective("collect", {"target_id": "basket", "required_qty": 1}, "Craftea 1 Cesta")],
             [Reward("water", 6), Reward("rope", 1)]),
        ]

        for mid, title, lore, objs, rewards in mini:
            M.append(Mission(mid, title, lore, objs, [Reward(r.item_id, r.qty) if isinstance(r, Reward) else Reward(r[0], r[1]) for r in rewards]))

        return M

    # ---- Actualización / consulta ----

    def _make_context(self) -> MissionContext:
        # Hook especial para la variedad de semillas: mapeamos en flags el conteo actual.
        seed_ids = [iid for iid in getattr(self.inventory, "item_database", {}).keys() if iid.startswith("seed_")]
        unique = sum(1 for sid in seed_ids if self.inventory.count_item(sid) > 0)
        # guardamos el progreso de este objetivo sintético como si fuera un flag
        flags = dict(self.flags)
        flags["variety_seeds"] = unique
        return MissionContext(self.inventory, self.visited_scenes, self.slept_count, flags)

    def update(self) -> None:
        ctx = self._make_context()
        # Parche para objetivo sintético (variedad de semillas)
        for m in self.missions:
            for obj in m.objectives:
                if obj.kind == "collect" and obj.params.get("target_id") == "VAR_SEEDS_6":
                    # Sobrescribimos el progress en runtime usando flag "variety_seeds"
                    obj.progress = lambda c, need=int(obj.params.get("required_qty", 6)): (min(int(c.flags.get("variety_seeds", 0)), need), need)
                    obj.is_done = lambda c, need=int(obj.params.get("required_qty", 6)): int(c.flags.get("variety_seeds", 0)) >= need  # type: ignore
        for m in self.missions:
            m.update_state(ctx)

    def is_completed(self, idx: int) -> bool:
        return 0 <= idx < len(self.missions) and self.missions[idx].completed

    def can_claim(self, idx: int) -> bool:
        return (0 <= idx < len(self.missions)
                and self.missions[idx].completed
                and not self.missions[idx].claimed)

    def claim(self, idx: int) -> bool:
        if not self.can_claim(idx):
            return False
        m = self.missions[idx]
        # Otorgar recompensas
        for r in m.rewards:
            try:
                self.inventory.add_item(r.item_id, r.qty)
            except Exception:
                pass
        m.claimed = True
        return True

    # ---- Eventos desde Game ----
    def on_enter_scene(self, scene_id: int) -> None:
        self.visited_scenes.add(int(scene_id))

    def on_sleep(self) -> None:
        self.slept_count += 1

    def on_open_diary(self) -> None:
        self.flags["opened_missions"] = True

    # ---- Persistencia ----
    def export_state(self) -> Dict[str, Any]:
        return {
            "visited": sorted(list(self.visited_scenes)),
            "slept": int(self.slept_count),
            "flags": dict(self.flags),
            "missions": [
                {"id": m.mission_id, "completed": bool(m.completed), "claimed": bool(m.claimed)}
                for m in self.missions
            ],
            "selected": int(self.selected_index),
            "open": bool(self.is_open),
        }

    def import_state(self, data: Dict[str, Any]) -> None:
        if not data:
            return
        self.visited_scenes = set(int(x) for x in data.get("visited", [1]) if isinstance(x, (int, float)))
        self.slept_count = int(data.get("slept", 0))
        flags = data.get("flags", {})
        if isinstance(flags, dict):
            self.flags = {str(k): bool(v) if isinstance(v, bool) else v for k, v in flags.items()}
        # Reconciliar misiones por id
        id_to_m = {m.mission_id: m for m in self.missions}
        for e in data.get("missions", []):
            mid = str(e.get("id", ""))
            if mid in id_to_m:
                mm = id_to_m[mid]
                mm.completed = bool(e.get("completed", False))
                mm.claimed = bool(e.get("claimed", False))
        self.selected_index = int(data.get("selected", 0))
        self.is_open = bool(data.get("open", False))
        # Re-evaluar con contexto actual para no quedar “congelado”
        self.update()
