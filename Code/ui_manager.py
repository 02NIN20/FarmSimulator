# ui_manager.py

from __future__ import annotations
from typing import Optional, List, Any
from pyray import *
from math import sin
from random import get_random_value

# Importaciones de módulos auxiliares y de managers
import ui_helpers
from asset_manager import AssetManager
from game_config import PAUSE_TAB_MAIN, TRANSITION_TIME, FADE_TIME 

# Definiciones de tipo para evitar dependencias circulares (solo para 'draw_play_state')
class Scene: pass
class Player: pass
class MapSystem: pass
class Inventory: pass
class CraftingSystem: pass
class FurnaceSystem: pass
class GameClock: pass
class SaveManager: pass


class UIManager:
    """Gestiona la lógica, el estado y el dibujo de todos los menús, UI y efectos visuales."""
    
    def __init__(self, screen_w: int, screen_h: int, assets: AssetManager, initial_ui_state: dict) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.assets = assets
        self.ui_state = initial_ui_state
        
        # Estado de Menú Principal
        self.main_menu = {"t": 0.0, "selected": 0, "credits_open": False, "theme": "Primavera", "particles": []}
        self.init_main_menu_theme()
        
        # Estado de Interacción (Modals, Input)
        self.newgame_modal_open = False
        self.newgame_name = ""
        self.rename_slot_id: str | None = None
        self.rename_buffer: str = ""
        self.death_load_modal_open = False

        self._fsz = lambda base: ui_helpers.calc_font(self.screen_h, base)
        
    # --- MÉTODOS DE HELPERS Y LÓGICA DE UI ---
    
    # Aquí irían los métodos: _draw_text_custom, _draw_text_shadow, _draw_panel, _menu_button (copiados de game.py)
    # y la lógica de input (handle_newgame_name_input) y efectos (init_main_menu_theme, update_menu_fx).
    
    def handle_newgame_name_input(self) -> None:
        # ... Lógica original de manejo de entrada de texto ...
        key = get_char_pressed()
        while key > 0:
            if 32 <= key <= 125 and len(self.newgame_name) < 20:
                self.newgame_name += chr(key)
            key = get_char_pressed()
        if is_key_pressed(KEY_BACKSPACE) and len(self.newgame_name) > 0:
            self.newgame_name = self.newgame_name[:-1]
        if is_key_pressed(KEY_SPACE) and len(self.newgame_name) < 20:
             self.newgame_name += " "

    def init_main_menu_theme(self) -> None:
        # ... Lógica original de inicialización de partículas ...
        themes = ["Primavera", "Verano", "Otoño", "Invierno"]
        theme = themes[get_random_value(0, len(themes) - 1)]
        self.main_menu["theme"] = theme
        w, h = self.screen_w, self.screen_h
        particles = []
        # (Lógica de poblar la lista 'particles' según el tema)
        # ...
        self.main_menu["particles"] = particles

    def update_menu_fx(self, dt: float) -> None:
        # ... Lógica original de actualización de partículas ...
        m = self.main_menu
        m["t"] += dt
        theme = m.get("theme", "Primavera")
        w, h = self.screen_w, self.screen_h
        # (Lógica de mover las partículas según el tema)
        # ...
        pass
            
    # --- MÉTODOS DE DIBUJO DE ESTADO ---

    def draw_main_menu(self, activate_callback: callable) -> None:
        # ... Lógica de dibujo del menú principal (requiere los helpers _draw_text_shadow, _menu_button)
        pass

    def draw_config(self) -> None:
        # ... Lógica de dibujo de la configuración (usa self.ui_state y ui_helpers)
        pass
        
    def draw_save_slots(self, save_mgr: SaveManager) -> None:
        # ... Lógica de dibujo de slots de guardado (usa self.newgame_modal_open, self.newgame_name, save_mgr)
        pass

    def draw_play_state(self, scene: Scene, player: Player, camera: Camera2D, 
                        map_system: MapSystem, inventory: Inventory, crafting: CraftingSystem, 
                        furnace: FurnaceSystem, ingame_menu_open: bool, player_dead: bool, 
                        clock: GameClock) -> None:
        """Dibuja el HUD, Inventario, Menú de Pausa, Mapa, etc."""
        # ... Lógica de dibujo del estado PLAY (delegando a los objetos de juego)
        
        # Ejemplo: Dibujar el mapa y el inventario
        # map_system.draw_minimap(...)
        # inventory.draw(...) 
        # ...
        pass

    def draw_loading_overlay(self, loading: bool, trans_elapsed: float) -> None:
        """Dibuja la pantalla de transición/carga."""
        if not loading: return
        
        # ... Lógica de fade in/out basada en trans_elapsed, TRANSITION_TIME, FADE_TIME ...
        # ... Uso de self.assets.loading_texture ...
        pass