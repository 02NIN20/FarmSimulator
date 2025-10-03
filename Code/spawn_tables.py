# spawn_tables.py
# Tablas de aparición (loot de suelo) por escenario.
# - Sin "tierras" ni "fertilizantes" (se obtienen/craftean).
# - first_count: (min, max) de objetos que se generan la PRIMERA VEZ que entras al mapa.
# - repeat_count: (min, max) objetivo al reingresar; si el mapa quedó por debajo del mínimo,
#   se repone una cantidad pequeña (hasta el máximo).
# - items: id del ítem -> {"w": peso relativo, "qty": (min, max) por pickup}
#
# Nota: los IDs de semillas y materiales corresponden a items definidos en items_registry.py.

from __future__ import annotations
from typing import Dict

SPAWN_TABLES: Dict[int, dict] = {
    1: {  # Escenario 1 — Genérico / Agricultura local
        "first_count":  (35, 50),
        "repeat_count": (8, 16),
        "items": {
            "leaves":            {"w": 30, "qty": (1, 3)},
            "wood_branch":       {"w": 24, "qty": (1, 2)},
            "rock":              {"w": 18, "qty": (1, 2)},
            "seed_corn":         {"w": 12, "qty": (1, 2)},
            "seed_spring_wheat": {"w": 12, "qty": (1, 2)},
            "seed_carrot":       {"w": 10, "qty": (1, 2)},
            "seed_cabbage":      {"w": 10, "qty": (1, 2)},
            "log_small":         {"w": 6,  "qty": (1, 1)},
            "rope_fiber":        {"w": 4,  "qty": (1, 2)},
            "log":               {"w": 3,  "qty": (1, 1)},
            "clay":              {"w": 3,  "qty": (1, 2)},
            "honeycomb_fragment":{"w": 1,  "qty": (1, 1)},
        }
    },
    2: {  # Escenario 2 — Alaska (Valle Matanuska–Susitna)
        "first_count":  (40, 60),
        "repeat_count": (10, 18),
        "items": {
            "leaves":             {"w": 26, "qty": (1, 3)},
            "wood_branch":        {"w": 20, "qty": (1, 2)},
            "rock":               {"w": 18, "qty": (1, 2)},
            "seed_potato":        {"w": 12, "qty": (1, 2)},
            "seed_kale":          {"w": 10, "qty": (1, 2)},
            "seed_raspberry_ht":  {"w": 7,  "qty": (1, 1)},
            "seed_spring_barley": {"w": 7,  "qty": (1, 2)},
            "seed_spring_wheat":  {"w": 7,  "qty": (1, 2)},
            "log_small":          {"w": 5,  "qty": (1, 1)},
            "ore_copper":         {"w": 3,  "qty": (1, 2)},
            "ore_iron":           {"w": 2,  "qty": (1, 2)},
            "ore_coal":           {"w": 1,  "qty": (1, 2)},
            "log":                {"w": 1,  "qty": (1, 1)},
            "honeycomb_fragment": {"w": 1,  "qty": (1, 1)},
        }
    },
    3: {  # Escenario 3 — Dakota del Norte (PPR, Woodworth)
        "first_count":  (38, 56),
        "repeat_count": (9, 17),
        "items": {
            "leaves":             {"w": 22, "qty": (1, 3)},
            "rock":               {"w": 18, "qty": (1, 2)},
            "seed_canola":        {"w": 12, "qty": (1, 2)},
            "seed_field_pea":     {"w": 12, "qty": (1, 2)},
            "seed_spring_wheat":  {"w": 10, "qty": (1, 2)},
            "seed_sunflower":     {"w": 10, "qty": (1, 2)},
            "seed_malting_barley":{"w": 8,  "qty": (1, 2)},
            "seed_soy":           {"w": 8,  "qty": (1, 2)},
            "wood_branch":        {"w": 6,  "qty": (1, 2)},
            "log_small":          {"w": 3,  "qty": (1, 1)},
            "clay":               {"w": 2,  "qty": (1, 2)},
            "ore_iron":           {"w": 2,  "qty": (1, 2)},
            "honeycomb_fragment": {"w": 1,  "qty": (1, 1)},
        }
    },
    4: {  # Escenario 4 — Michigan (Suttons Bay – Leelanau)
        "first_count":  (40, 60),
        "repeat_count": (10, 18),
        "items": {
            "leaves":                 {"w": 24, "qty": (1, 3)},
            "wood_branch":            {"w": 18, "qty": (1, 2)},
            "rock":                   {"w": 14, "qty": (1, 2)},
            "seed_blueberry":         {"w": 10, "qty": (1, 2)},
            "seed_apple":             {"w": 9,  "qty": (1, 2)},
            "seed_cold_hybrid_grape": {"w": 9,  "qty": (1, 2)},
            "seed_asparagus":         {"w": 9,  "qty": (1, 2)},
            "seed_pickling_cucumber": {"w": 9,  "qty": (1, 2)},
            "seed_tart_cherry":       {"w": 6,  "qty": (1, 2)},
            "log_small":              {"w": 4,  "qty": (1, 1)},
            "clay":                   {"w": 3,  "qty": (1, 2)},
            "ore_iron":               {"w": 2,  "qty": (1, 2)},
            "ore_copper":             {"w": 1,  "qty": (1, 2)},
            "log":                    {"w": 1,  "qty": (1, 1)},
            "honeycomb_fragment":     {"w": 1,  "qty": (1, 1)},
        }
    },
}
