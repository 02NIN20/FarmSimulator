# animal_spawns.py
from __future__ import annotations
from typing import Dict, List
from random import randint, choices
from pyray import *
from animals import Animal, AnimalSpec

# Especies por bioma/escena (índice de escena +1)
# Orden de AnimalSpec: name, friendly, color, size, max_hp, speed, detect_range=0, attack_range=0, dps=0, hit_cooldown=0.8
ANIMAL_TABLES: Dict[int, dict] = {
    1: {  # genérico
        "first_count":  (6, 10),
        "repeat_count": (2, 4),
        "species": {
            # amistosos (granja)
            "hen":   {"w": 6, "spec": AnimalSpec("Gallina", True,  Color(230,230,180,255), 18, 30.0, 70.0)},
            "chick": {"w": 4, "spec": AnimalSpec("Pollo",   True,  Color(255,245,180,255), 12, 18.0, 60.0)},
            "duck":  {"w": 3, "spec": AnimalSpec("Pato",    True,  Color(180,210,230,255), 18, 26.0, 70.0)},
            "pig":   {"w": 3, "spec": AnimalSpec("Cerdo",   True,  Color(225,170,170,255), 22, 40.0, 55.0)},
            "cow":   {"w": 2, "spec": AnimalSpec("Vaca",    True,  Color(170,170,150,255), 26, 60.0, 50.0)},
            # salvajes
            "boar":  {"w": 2, "spec": AnimalSpec("Jabalí", False, Color(110,80,70,255),   22, 55.0, 85.0, detect_range=220.0, attack_range=30.0, dps=12.0, hit_cooldown=0.7)},
            "wolf":  {"w": 1, "spec": AnimalSpec("Lobo",   False, Color(120,120,120,255), 20, 45.0, 110.0, detect_range=260.0, attack_range=32.0, dps=10.0, hit_cooldown=0.55)},
        }
    },
    2: {  # Alaska
        "first_count":  (7, 11),
        "repeat_count": (2, 4),
        "species": {
            "duck":  {"w": 5, "spec": AnimalSpec("Pato", True,  Color(180,210,230,255), 18, 26.0, 70.0)},
            "hen":   {"w": 4, "spec": AnimalSpec("Gallina", True, Color(230,230,180,255), 18, 30.0, 70.0)},
            "moose": {"w": 2, "spec": AnimalSpec("Alce", False, Color(120,90,60,255), 28, 90.0, 75.0, detect_range=260.0, attack_range=34.0, dps=14.0, hit_cooldown=0.9)},
            "wolf":  {"w": 2, "spec": AnimalSpec("Lobo", False, Color(120,120,120,255), 20, 45.0, 110.0, detect_range=280.0, attack_range=32.0, dps=10.0, hit_cooldown=0.55)},
        }
    },
    3: {  # PPR / praderas
        "first_count":  (6, 10),
        "repeat_count": (2, 4),
        "species": {
            "cow":   {"w": 4, "spec": AnimalSpec("Vaca", True,  Color(170,170,150,255), 26, 60.0, 50.0)},
            "pig":   {"w": 3, "spec": AnimalSpec("Cerdo", True, Color(225,170,170,255), 22, 40.0, 55.0)},
            "hen":   {"w": 3, "spec": AnimalSpec("Gallina", True, Color(230,230,180,255), 18, 30.0, 70.0)},
            "coyote":{"w": 2, "spec": AnimalSpec("Coyote", False, Color(150,120,90,255), 18, 40.0, 105.0, detect_range=240.0, attack_range=30.0, dps=9.0, hit_cooldown=0.6)},
        }
    },
    4: {  # Michigan / bosques y lagos
        "first_count":  (7, 11),
        "repeat_count": (2, 4),
        "species": {
            "duck":  {"w": 4, "spec": AnimalSpec("Pato", True, Color(180,210,230,255), 18, 26.0, 70.0)},
            "hen":   {"w": 3, "spec": AnimalSpec("Gallina", True, Color(230,230,180,255), 18, 30.0, 70.0)},
            "deer":  {"w": 3, "spec": AnimalSpec("Ciervo", False, Color(155,120,90,255), 20, 50.0, 95.0, detect_range=220.0, attack_range=28.0, dps=8.0, hit_cooldown=0.7)},
            "bear":  {"w": 1, "spec": AnimalSpec("Oso", False, Color(95,70,55,255), 28, 120.0, 80.0, detect_range=260.0, attack_range=36.0, dps=16.0, hit_cooldown=1.0)},
        }
    },
}

class AnimalManager:
    def __init__(self) -> None:
        self.animals_by_scene: Dict[int, List[Animal]] = {}
        self.visited: Dict[int, int] = {}

    def _random_inside(self, scene_size: Vector2, polygon=None) -> Vector2:
        # muestreo por rechazo simple si hay polígono
        for _ in range(400):
            x = randint(20, int(scene_size.x) - 20)
            y = randint(20, int(scene_size.y) - 20)
            if not polygon:
                return Vector2(x, y)
            # punto dentro del polígono (ray casting simple)
            inside = False
            n = len(polygon)
            for i in range(n):
                j = (i - 1) % n
                xi, yi = polygon[i].x, polygon[i].y
                xj, yj = polygon[j].x, polygon[j].y
                inter = ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi)
                if inter:
                    inside = not inside
            if inside:
                return Vector2(x, y)
        return Vector2(scene_size.x * 0.5, scene_size.y * 0.5)

    def _roll_species(self, scene_id: int, count: int) -> List[AnimalSpec]:
        tbl = ANIMAL_TABLES.get(scene_id, ANIMAL_TABLES[1])
        entries = list(tbl["species"].values())
        weights = [e["w"] for e in entries]
        specs = [e["spec"] for e in entries]
        picked = choices(specs, weights=weights, k=max(0, count))
        return picked

    def on_enter_scene(self, scene_id: int, scene_size: Vector2, polygon=None) -> None:
        times = self.visited.get(scene_id, 0)
        first = times == 0
        self.visited[scene_id] = times + 1
        lst = self.animals_by_scene.setdefault(scene_id, [])
        existing = len([a for a in lst if a.alive])

        tbl = ANIMAL_TABLES.get(scene_id, ANIMAL_TABLES[1])
        rng = tbl["first_count"] if first else tbl["repeat_count"]
        target = randint(rng[0], rng[1])
        to_add = max(0, target - existing)
        if to_add <= 0:
            return

        for spec in self._roll_species(scene_id, to_add):
            pos = self._random_inside(scene_size, polygon)
            lst.append(Animal(spec, pos))

    def update(self, scene_id: int, dt: float, player_pos: Vector2) -> List[float]:
        """Actualiza y devuelve daños al jugador (lista por golpe)."""
        lst = self.animals_by_scene.get(scene_id, [])
        damages: List[float] = []
        for a in lst:
            hit, dmg = a.update(dt, player_pos)
            if hit and dmg > 0:
                damages.append(dmg)
        # elimina caídos
        self.animals_by_scene[scene_id] = [a for a in lst if a.alive]
        return damages

    def draw(self, scene_id: int) -> None:
        for a in self.animals_by_scene.get(scene_id, []):
            a.draw()

    def damage_in_radius(self, scene_id: int, center: Vector2, radius: float, damage: float) -> int:
        """Aplica daño a animales en un radio y devuelve cuántos impactó."""
        hit = 0
        for a in self.animals_by_scene.get(scene_id, []):
            if not a.alive:
                continue
            dx = a.pos.x - center.x
            dy = a.pos.y - center.y
            if (dx*dx + dy*dy) ** 0.5 <= radius + a.spec.size * 0.5:
                a.take_damage(damage)
                hit += 1
        return hit
