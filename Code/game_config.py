# game_config.py

from __future__ import annotations
from typing import Optional, List, Tuple
from pyray import Color, Vector2 # Solo por tipo

# ----------------- Configuración Global -----------------
RESOLUTIONS: List[Tuple[int, int]] = [
    (1920, 1080), (1600, 900), (1366, 768),
    (1280, 720), (1024, 576), (960, 540),
]

MIN_ZOOM, MAX_ZOOM = 0.35, 3.0
TRANSITION_TIME = 3.0
FADE_TIME = 0.5
HOLD_TIME = max(0.0, TRANSITION_TIME - 2.0 * FADE_TIME)
LOADING_IMAGE_PATH: str | None = None

# ----------------- Estados del Juego -----------------
STATE_MAIN_MENU   = "MAIN_MENU"
STATE_CONFIG      = "CONFIG"
STATE_PLAY        = "PLAY"
STATE_LOADING     = "LOADING"
STATE_SAVE_SLOTS  = "SAVE_SLOTS"

# ----------------- Pestañas de Pausa -----------------
PAUSE_TAB_MAIN  = "MAIN"
PAUSE_TAB_VIDEO = "VIDEO"
PAUSE_TAB_AUDIO = "AUDIO"
PAUSE_TAB_GAME  = "GAME"