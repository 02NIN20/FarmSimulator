# Code/animals.py
from __future__ import annotations
from typing import Dict, Tuple, Optional
from pyray import (
    load_texture, unload_texture, draw_texture_ex,
    Vector2, Texture2D, WHITE
)

# ------------------------------------------------------------
# Especificaciones de cada especie
# ------------------------------------------------------------

class AnimalSpec:
    """
    Define el 'modelo' de una especie.
    - name: id de la especie (cow, pig, wolf, duck, etc.)
    - speed: velocidad base de desplazamiento
    - hp: vida máxima
    - damage: daño al jugador por contacto/ataque
    - aggro_radius: radio en el que persigue al jugador (si 0 => no agresivo)
    - wander_speed: velocidad en modo vagar
    - size: tamaño base para el render (escala del sprite)
    """
    def __init__(
        self,
        name: str,
        speed: float,
        hp: float,
        damage: float,
        aggro_radius: float,
        wander_speed: float,
        size: float = 32.0,
    ) -> None:
        self.name = name
        self.speed = float(speed)
        self.hp = float(hp)
        self.damage = float(damage)
        self.aggro_radius = float(aggro_radius)
        self.wander_speed = float(wander_speed)
        self.size = float(size)

# Mantén aquí especies antiguas o adicionales (no las borramos: “solo esconder” ≈ no spawnear)
SPECS: Dict[str, AnimalSpec] = {
    # Nuevas/solicitadas
    "cow":  AnimalSpec("cow",  60.0, 120.0,  0.0,   0.0, 30.0, size=42.0),  # vaca: pasiva
    "pig":  AnimalSpec("pig",  70.0,  60.0,  0.0,   0.0, 36.0, size=36.0),  # cerdo: pasivo
    "wolf": AnimalSpec("wolf", 95.0,  80.0, 10.0, 220.0, 40.0, size=34.0),  # lobo: agresivo
    "duck": AnimalSpec("duck", 80.0,  40.0,  0.0,   0.0, 44.0, size=28.0),  # pato: pasivo

    # Ejemplos “ocultos” (se pueden tener, pero no spawneamos)
    "bear": AnimalSpec("bear", 70.0, 180.0, 20.0, 250.0, 30.0, size=46.0),
    "deer": AnimalSpec("deer", 90.0,  70.0,  0.0,   0.0, 50.0, size=38.0),
}

# ------------------------------------------------------------
# Registro global de sprites por especie y caché de texturas
# ------------------------------------------------------------

# Guarda rutas de sprites por especie: {"cow": {"left": "...", "right": "..."}, ...}
_SPECIES_SPRITES: Dict[str, Dict[str, str]] = {}

# Caché de texturas: {"cow": {"left": Texture2D, "right": Texture2D}, ...}
_SPRITE_CACHE: Dict[str, Dict[str, Optional[Texture2D]]] = {}

def register_species_sprites(mapping: dict) -> None:
    """
    Registra rutas de sprites por especie. Acepta:
    {
      "cow":  {"left": "assets/vacaizquierda.png",  "right": "assets/vacaderecha.png"},
      "pig":  {"left": "assets/cerdoizquierda.png", "right": "assets/cerdoderecha.png"},
      ...
    }
    También soporta tuplas/listas (right, left) pero se recomienda el dict.
    """
    global _SPECIES_SPRITES
    if not isinstance(mapping, dict):
        return

    for species_key, val in mapping.items():
        key = (species_key or "").strip().lower()
        if not key:
            continue

        left_path = None
        right_path = None
        if isinstance(val, dict):
            left_path  = val.get("left")
            right_path = val.get("right")
        else:
            # Soporte opcional (right, left)
            try:
                right_path, left_path = val
            except Exception:
                pass

        if not (left_path and right_path):
            continue

        _SPECIES_SPRITES[key] = {"left": str(left_path), "right": str(right_path)}
        # Al cambiar rutas, invalidamos el caché previo para esa especie
        if key in _SPRITE_CACHE:
            safe_unload_species(key)
            del _SPRITE_CACHE[key]

def get_registered_species_sprites(species: str) -> Tuple[Optional[str], Optional[str]]:
    d = _SPECIES_SPRITES.get((species or "").lower())
    if not d:
        return (None, None)
    return (d.get("right"), d.get("left"))

def get_textures_for(species: str) -> Dict[str, Optional[Texture2D]]:
    """
    Devuelve diccionario {"right": Texture2D|None, "left": Texture2D|None} para la especie.
    Carga desde disco si no estaba en caché.
    Si no hay rutas registradas, devuelve {"right": None, "left": None}.
    """
    key = (species or "").lower()

    # Si ya está cacheado, devolver
    cached = _SPRITE_CACHE.get(key)
    if cached is not None:
        return cached

    right_path, left_path = get_registered_species_sprites(key)
    result = {"right": None, "left": None}

    if right_path:
        try:
            result["right"] = load_texture(right_path)
        except Exception:
            result["right"] = None
    if left_path:
        try:
            result["left"] = load_texture(left_path)
        except Exception:
            result["left"] = None

    _SPRITE_CACHE[key] = result
    return result

def safe_unload_species(species: str) -> None:
    """Descarga texturas de una especie específica, si están cargadas."""
    key = (species or "").lower()
    d = _SPRITE_CACHE.get(key)
    if not d:
        return
    for side in ("left", "right"):
        tex = d.get(side)
        if tex:
            try:
                unload_texture(tex)
            except Exception:
                pass
            d[side] = None

def unload_all_textures() -> None:
    """Descarga todas las texturas cacheadas (llamar al cerrar el juego si quieres)."""
    for sp in list(_SPRITE_CACHE.keys()):
        safe_unload_species(sp)
    _SPRITE_CACHE.clear()

# ------------------------------------------------------------
# Helper opcional de dibujado (si quieres usarlo en otros lados)
# ------------------------------------------------------------

def draw_animal_sprite(species: str, pos: Vector2, facing_right: bool, size: float = 32.0) -> None:
    """
    Dibuja el sprite ya cacheado (si existe). Escala el sprite respecto a 'size'.
    Si no hay sprite registrado/cargado, no dibuja nada (para fallback usa geometría en tu Manager).
    """
    texs = get_textures_for(species)
    tex = texs["right"] if facing_right else texs["left"]
    if not tex:
        return
    # Escala manteniendo proporción para que el 'alto' ≈ size
    scale = size / max(1.0, float(tex.height))
    draw_texture_ex(tex, pos, 0.0, scale, WHITE)
