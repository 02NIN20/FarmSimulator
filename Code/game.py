# game.py (Motor Orquestador)

from __future__ import annotations
from typing import Optional, List, Tuple, Any
from pyray import *

# --- Importaciones de Módulos ---
from player import Player
from scene import Scene
import input_handler
from inventory import Inventory # Asumimos Inventory o InventoryUIController
from map_system import MapSystem
from ground_spawns import SpawnManager
from save_system import SaveManager
from animal_spawns import AnimalManager
from crafting_system import CraftingSystem, CRAFTING_RECIPES
from furnace_system import FurnaceSystem, SMELTING_RECIPES, COMBUSTIBLES

# --- Importaciones de Clases Refactorizadas ---
from game_config import (
    RESOLUTIONS, STATE_MAIN_MENU, STATE_CONFIG, STATE_PLAY, 
    STATE_LOADING, STATE_SAVE_SLOTS, PAUSE_TAB_MAIN
)
from game_clock import GameClock
from asset_manager import AssetManager
from world_manager import WorldManager
from ui_manager import UIManager


class Game:
    def __init__(self, initial_res_index: int) -> None:
        # 1. Inicialización de Ventana (se mantiene)
        self.res_index = initial_res_index
        self.screen_w, self.screen_h = RESOLUTIONS[self.res_index]
        self.scene_w, self.scene_h = self.screen_w * 5, self.screen_h * 5
        init_window(self.screen_w, self.screen_h, "ASTRA - NASA Space Apps")
        set_exit_key(0)
        # ... otros estados y configuración de ventana ...
        
        # 2. Inicialización de Estados
        self.state = STATE_MAIN_MENU
        self.running = True
        self.ingame_menu_open = False
        # ...
        
        # 3. Managers
        self.assets = AssetManager()
        self.world_mgr = WorldManager(self.scene_w, self.scene_h)
        self.ui_mgr = UIManager(self.screen_w, self.screen_h, self.assets, self._get_initial_ui_state()) # Usa un helper
        
        # 4. Sistemas Centrales
        self.clock = GameClock(seconds_per_day=300.0)
        self.save_mgr = SaveManager("saves")
        
        # 5. Entidades de Juego (usando WorldManager para escenas)
        self.scenes = self.world_mgr.scenes
        self.active_scene_index = 0
        self.player = Player(self.world_mgr.scene_center(self.scenes[self.active_scene_index]))
        self.inventory = Inventory(rows=4, cols=10)
        self.map_system = MapSystem(total_scenes=len(self.scenes))
        # ... Resto de sistemas (spawns, animals, crafting, furnace) ...
        self.spawns = SpawnManager(self.inventory)
        self.animals = AnimalManager()
        self.crafting = CraftingSystem()
        self.furnace = FurnaceSystem()

        # 6. Cámara (se mantiene)
        self.camera = Camera2D()
        self._update_camera_offset()
        self.camera.target = Vector2(self.player.position.x, self.player.position.y)
        self.camera.zoom = 1.0
        
    def _get_initial_ui_state(self) -> dict:
        # Mantiene el estado inicial de la UI en el motor
        return {
            "master_volume": 1.0, "music_volume": 0.8, "sfx_volume": 0.9,
            "music_dragging": False, "sfx_dragging": False, "master_dragging": False,
            "brightness": 0.5, "brightness_dragging": False, "show_grid": True,
            "show_fps": False, "res_dropdown_open": False, "pause_tab": PAUSE_TAB_MAIN,
            "fullscreen": False,
        }

    # ---------- _handle_input (Delega al UIManager la gestión de input de menús) ----------
    def _handle_input(self) -> None:
        if self.state == STATE_MAIN_MENU:
            # Lógica de navegación principal (UP/DOWN/ENTER)
            labels = ["Jugar", "Configuración", "Créditos", "Salir"]
            if is_key_pressed(KEY_UP):
                self.ui_mgr.main_menu["selected"] = (self.ui_mgr.main_menu["selected"] - 1) % len(labels)
            if is_key_pressed(KEY_DOWN):
                self.ui_mgr.main_menu["selected"] = (self.ui_mgr.main_menu["selected"] + 1) % len(labels)
            if is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_KP_ENTER):
                self._activate_main_menu_item(labels[self.ui_mgr.main_menu["selected"]])
            if is_key_pressed(KEY_T):
                self.ui_mgr.init_main_menu_theme() # Delega
        
        if self.state == STATE_SAVE_SLOTS:
            # Lógica de escape y manejo de input para el modal de nueva partida
            if is_key_pressed(KEY_ESCAPE):
                if self.ui_mgr.rename_slot_id:
                    self.ui_mgr.rename_slot_id = None
                elif self.ui_mgr.newgame_modal_open:
                    self.ui_mgr.newgame_modal_open = False
                else:
                    self.state = STATE_MAIN_MENU
                    self.ui_mgr.init_main_menu_theme()
            
            if self.ui_mgr.newgame_modal_open:
                self.ui_mgr.handle_newgame_name_input() # Delega

        # ... Resto de la lógica de input (play state) se mantiene ...

    def _activate_main_menu_item(self, label: str) -> None:
        # Lógica de cambio de estado (se mantiene en el motor)
        if label == "Jugar":
            self.state = STATE_SAVE_SLOTS
        elif label == "Configuración":
            self.state = STATE_CONFIG
            self.ui_mgr.ui_state["res_dropdown_open"] = False
        elif label == "Créditos":
            self.ui_mgr.main_menu["credits_open"] = True
        elif label == "Salir":
            self.running = False


    # ---------- _update (Orquestación) ----------
    def _update(self, dt: float) -> None:
        if self.state == STATE_MAIN_MENU:
            self.ui_mgr.update_menu_fx(dt) # Delega

        # Lógica en juego
        if (self.state == STATE_PLAY and not self.loading and
            not self.ingame_menu_open and not self.inventory.is_open and not self.map_system.is_open
            and not self.crafting.is_open and not self.furnace.is_open):
            
            # ... Lógica de movimiento, colisiones, etc. ...
            pass 

        # Actualizar sistemas
        if self.state == STATE_PLAY and not self.loading and not self.player_dead:
            self.furnace.update(dt)
        if not self.ingame_menu_open and not self.player_dead:
            self.clock.update(dt) # Delega


    # ---------- _draw (Delega a UIManager) ----------
    def _draw(self) -> None:
        begin_drawing()
        clear_background(RAYWHITE)
        
        if self.state == STATE_MAIN_MENU:
            self.ui_mgr.draw_main_menu(self._activate_main_menu_item)
        elif self.state == STATE_CONFIG:
            self.ui_mgr.draw_config()
        elif self.state == STATE_SAVE_SLOTS:
            self.ui_mgr.draw_save_slots(self.save_mgr)
        elif self.state in (STATE_PLAY, STATE_LOADING):
            # Dibuja el estado PLAY y la pantalla de carga (delegando los sistemas)
            self.ui_mgr.draw_play_state(
                scene=self.scenes[self.active_scene_index], player=self.player, 
                camera=self.camera, map_system=self.map_system, inventory=self.inventory, 
                crafting=self.crafting, furnace=self.furnace, ingame_menu_open=self.ingame_menu_open, 
                player_dead=self.player_dead, clock=self.clock
            )
            self.ui_mgr.draw_loading_overlay(self.loading, self.trans_elapsed) 
        
        end_drawing()
        
    def run(self) -> None:
        # Bucle principal (se mantiene en el motor)
        while self.running and not window_should_close():
            dt = get_frame_time()
            self._handle_input()
            self._update(dt)
            self._draw()
        self.assets.unload_assets() # Delega la limpieza
        close_window()