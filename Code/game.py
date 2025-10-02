# game.py

from __future__ import annotations
from pyray import *
from player import Player
from scene import Scene
import input_handler
import ui_helpers
from inventory import Inventory
from map_system import MapSystem
from typing import Optional

# Definiciones de constantes
RESOLUTIONS = [
    (1920, 1080),
    (1600, 900),
    (1366, 768),
    (1280, 720),
    (1024, 576),
    (960, 540),
]
MIN_ZOOM, MAX_ZOOM = 0.35, 3.0
TRANSITION_TIME = 3.0
FADE_TIME = 0.5
HOLD_TIME = max(0.0, TRANSITION_TIME - 2.0 * FADE_TIME)
LOADING_IMAGE_PATH: str | None = None

# Estados del juego
STATE_MAIN_MENU = "MAIN_MENU"
STATE_CONFIG = "CONFIG"
STATE_PLAY = "PLAY"
STATE_LOADING = "LOADING"

class Game:
    """Clase principal que gestiona el juego, los estados, la UI y la cámara."""

    def __init__(self, initial_res_index: int) -> None:

        # Propiedades de ventana
        self.res_index = initial_res_index
        self.screen_w, self.screen_h = RESOLUTIONS[self.res_index]
        self.scene_w, self.scene_h = self.screen_w * 5, self.screen_h * 5
        
        # Inicialización de Raylib
        init_window(self.screen_w, self.screen_h, "Juego NASA Space Apps 2025")
        set_target_fps(60)

        # Estados
        self.state = STATE_MAIN_MENU
        self.running = True
        self.ingame_menu_open = False
        self.loading = False
        self.trans_elapsed = 0.0
        self.target_scene: Optional[int] = None
        self.swapped = False
        self.post_load_state = STATE_PLAY

        # Datos del mundo
        self.scenes = self._create_scenes()
        self.active_scene_index = 0
        self.player = Player(self._scene_center(self.scenes[self.active_scene_index]))
        
        # *** NUEVOS SISTEMAS: INVENTARIO Y MAPA ***
        self.inventory = Inventory(rows=4, cols=10)
        self.map_system = MapSystem(total_scenes=len(self.scenes))
        
        # Añadir items iniciales al inventario (para probar)
        self.inventory.add_item("seed_corn", 10)
        self.inventory.add_item("seed_wheat", 5)
        self.inventory.add_item("water", 20)
        self.inventory.add_item("fertilizer", 8)
        # ******************************************

        # Cámara
        self.camera = Camera2D()
        self._update_camera_offset()
        self.camera.target = Vector2(self.player.position.x, self.player.position.y)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        # UI State
        self.ui_state = {
            "music_volume": 0.8,
            "sfx_volume": 0.9,
            "music_dragging": False,
            "sfx_dragging": False,
            "res_dropdown_open": False,
        }
        
        # Textura de carga (opcional)
        self.loading_texture: Optional[Texture2D] = None 
        self._load_assets()

    # --- Setup Helpers ---

    def _update_camera_offset(self) -> None:
        """Actualiza el offset de la cámara al centro de la pantalla."""
        self.camera.offset = Vector2(self.screen_w / 2, self.screen_h / 2)

    def _make_scene(self, scene_id: int, color: Color) -> Scene:
        size = Vector2(self.scene_w, self.scene_h)
        spawn = Vector2(self.scene_w * 0.5, self.scene_h * 0.5)
        return Scene(scene_id, size, color, spawn)

    def _create_scenes(self) -> list[Scene]:
        """Recrea todas las escenas."""
        return [
            self._make_scene(1, Color(70, 120, 200, 255)),
            self._make_scene(2, Color(200, 120, 70, 255)),
            self._make_scene(3, Color(80, 160, 110, 255)),
            self._make_scene(4, Color(160, 80, 160, 255)),
        ]

    def _scene_center(self, scene: Scene) -> Vector2:
        return Vector2(scene.size.x * 0.5, scene.size.y * 0.5)

    def _load_assets(self) -> None:
        if LOADING_IMAGE_PATH is not None:
            try:
                self.loading_texture = load_texture(LOADING_IMAGE_PATH)
            except Exception:
                print(f"Error loading texture from: {LOADING_IMAGE_PATH}")
                self.loading_texture = None

    def _unload_assets(self) -> None:
        if self.loading_texture is not None:
            unload_texture(self.loading_texture)
            self.loading_texture = None

    # --- Game Loop Methods ---

    def run(self) -> None:
        """Bucle principal del juego."""
        while self.running and not window_should_close():
            dt = get_frame_time()
            self._handle_input()
            self._update(dt)
            self._draw()
        
        self._unload_assets()
        close_window()

    def _handle_input(self) -> None:
        """Gestiona las entradas de usuario."""
        
        # DEBUG: Imprimir cuando se presionan teclas
        if is_key_pressed(KEY_I):
            print("Tecla I presionada")
            print(f"Estado: {self.state}, Loading: {self.loading}")
        if is_key_pressed(KEY_M):
            print("Tecla M presionada")
            print(f"Estado: {self.state}, Loading: {self.loading}")
        
        # *** MANEJO DE INVENTARIO Y MAPA ***
        # Tecla I para inventario
        if self.state == STATE_PLAY and not self.loading:
            if is_key_pressed(KEY_I):
                if self.map_system.is_open:
                    self.map_system.is_open = False
                self.inventory.toggle()
        
        # Tecla M para mapa
        if self.state == STATE_PLAY and not self.loading:
            if is_key_pressed(KEY_M):
                if self.inventory.is_open:
                    self.inventory.is_open = False
                self.map_system.toggle()
        # ***********************************
        
        # ESC behavior
        if is_key_pressed(KEY_ESCAPE):
            if self.state == STATE_MAIN_MENU:
                self.running = False
            elif self.state == STATE_CONFIG:
                self.state = STATE_MAIN_MENU
                self.ui_state["res_dropdown_open"] = False
            elif self.state == STATE_PLAY:
                if self.inventory.is_open:
                    self.inventory.is_open = False
                elif self.map_system.is_open:
                    self.map_system.is_open = False
                else:
                    self.ingame_menu_open = not self.ingame_menu_open

        # P para menú in-game
        if self.state == STATE_PLAY and is_key_pressed(KEY_P):
            if self.inventory.is_open or self.map_system.is_open:
                self.inventory.is_open = False
                self.map_system.is_open = False
            else:
                self.ingame_menu_open = not self.ingame_menu_open
            
        # Cambio de escena con teclas 1-4
        if self.state == STATE_PLAY and not self.loading and not self.ingame_menu_open and not self.inventory.is_open and not self.map_system.is_open:
            requested = -1
            if is_key_pressed(KEY_ONE) or is_key_pressed(KEY_KP_1): requested = 0
            elif is_key_pressed(KEY_TWO) or is_key_pressed(KEY_KP_2): requested = 1
            elif is_key_pressed(KEY_THREE) or is_key_pressed(KEY_KP_3): requested = 2
            elif is_key_pressed(KEY_FOUR) or is_key_pressed(KEY_KP_4): requested = 3

            if requested != -1 and requested != self.active_scene_index:
                self._start_loading(requested, STATE_PLAY)

    def _update(self, dt: float) -> None:
        """Lógica de actualización del juego."""

        # Transition update
        if self.loading:
            self.trans_elapsed += dt
            if (not self.swapped) and (self.trans_elapsed >= FADE_TIME):
                if self.target_scene is not None:
                    self.active_scene_index = self.target_scene
                    self.player.position = self._scene_center(self.scenes[self.active_scene_index])
                    self.player.destination = self.player.position 
                    self.camera.target = Vector2(self.player.position.x, self.player.position.y)
                self.swapped = True
            if self.trans_elapsed >= TRANSITION_TIME:
                self._end_loading()
                self.state = self.post_load_state
                
        # Game updates (solo sin overlays)
        if self.state == STATE_PLAY and not self.loading and not self.ingame_menu_open and not self.inventory.is_open and not self.map_system.is_open:
            
            mouse_world_pos = get_screen_to_world_2d(get_mouse_position(), self.camera)
            player_input = input_handler.get_player_input(self.player.position, self.player.destination, mouse_world_pos)
            self.player.update(player_input, dt)

            # Zoom
            if is_key_down(KEY_EQUAL) or is_key_down(KEY_KP_ADD):
                self.camera.zoom += 1.0 * dt
            if is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT):
                self.camera.zoom -= 1.0 * dt
            self.camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.camera.zoom))

            self.camera.target = Vector2(self.player.position.x, self.player.position.y)

    def _start_loading(self, target_scene_index: int, next_state: str) -> None:
        """Inicia transición de carga."""
        self.loading = True
        self.trans_elapsed = 0.0
        self.target_scene = target_scene_index
        self.swapped = False
        self.post_load_state = next_state
        self.state = STATE_LOADING
        
    def _end_loading(self) -> None:
        """Finaliza transición."""
        self.loading = False
        self.trans_elapsed = 0.0
        self.target_scene = None
        self.swapped = False

    # --- Drawing Methods ---

    def _draw(self) -> None:
        """Lógica de dibujo."""
        begin_drawing()
        clear_background(RAYWHITE)
        draw_fps(20,20)

        ui_dims = ui_helpers.calculate_ui_dimensions(self.screen_w, self.screen_h)
        def fsz(base): return ui_helpers.calc_font(self.screen_h, base)
        
        if self.state == STATE_MAIN_MENU:
            self._draw_main_menu(ui_dims, fsz)
        elif self.state == STATE_CONFIG:
            self._draw_config_menu(ui_dims, fsz)
        elif self.state == STATE_PLAY:
            self._draw_play_state(ui_dims, fsz)
        elif self.state == STATE_LOADING:
            pass

        self._draw_loading_overlay(fsz)

        end_drawing()

    def _draw_main_menu(self, ui_dims: dict, fsz) -> None:
        """Dibuja el menú principal."""
        left_margin = ui_dims["left_margin"]
        bw = ui_dims["main_button_w"]
        bh = ui_dims["main_button_h"]
        x = left_margin
        
        draw_text("Mi Juego - Menu Principal", left_margin, 40, fsz(28), DARKGRAY)

        padding_bottom = int(self.screen_h * 0.04)
        gap = int(max(8, 12 * (self.screen_h / ui_helpers.REF_H)))
        start_y = self.screen_h - padding_bottom - (bh * 3 + gap * 2)

        if ui_helpers.draw_button_left(x, start_y + 0 * (bh + gap), bw, bh, "Iniciar", font_size=fsz(20)):
            self._start_loading(self.active_scene_index, STATE_PLAY)

        if ui_helpers.draw_button_left(x, start_y + 1 * (bh + gap), bw, bh, "Configuracion", font_size=fsz(20)):
            self.state = STATE_CONFIG

        if ui_helpers.draw_button_left(x, start_y + 2 * (bh + gap), bw, bh, "Salir", font_size=fsz(20)):
            self.running = False
            
        draw_text("Aqui ira la imagen/fondo del menu.", left_margin, start_y - 30, fsz(14), GRAY)

    def _draw_config_menu(self, ui_dims: dict, fsz) -> None:
        """Dibuja el menú de configuración."""
        left_margin = ui_dims["left_margin"]
        block_x = left_margin
        block_y = 110
        gap_y = int(max(8, 12 * (self.screen_h / ui_helpers.REF_H)))
        
        draw_text("Configuracion", left_margin, 28, fsz(28), DARKGRAY)
        draw_text("Resolucion", left_margin, 68, fsz(22), DARKGRAY)

        res_btn_w = ui_dims["button_w"]
        res_btn_h = ui_dims["button_h"]
        label = f"Resolucion: {RESOLUTIONS[self.res_index][0]} x {RESOLUTIONS[self.res_index][1]}"
        hovered, clicked = ui_helpers.button_left_rect(block_x, block_y, res_btn_w, res_btn_h, label, font_size=fsz(20))
        if clicked:
            self.ui_state["res_dropdown_open"] = not self.ui_state["res_dropdown_open"]

        if self.ui_state["res_dropdown_open"]:
            for i, (w, h) in enumerate(RESOLUTIONS):
                item_y = block_y + (i + 1) * (res_btn_h + 6)
                text_label = f"{w} x {h}"
                hovered_item, clicked_item = ui_helpers.button_left_rect(block_x, item_y, res_btn_w, res_btn_h, text_label, font_size=fsz(18))
                if clicked_item:
                    self.res_index = i
                    self.ui_state["res_dropdown_open"] = False
                    
        sl_start_y = block_y + (len(RESOLUTIONS) + 1) * (res_btn_h + 6) if self.ui_state["res_dropdown_open"] else block_y + (res_btn_h + 2 * gap_y)
        slider_w = ui_dims["slider_w"]
        slider_h = ui_dims["slider_h"]

        draw_text("Volumen Musica", block_x, sl_start_y, fsz(20), DARKGRAY)
        music_slider_y = sl_start_y + int(28 * (self.screen_h / ui_helpers.REF_H))
        self.ui_state["music_volume"] = ui_helpers.slider_horizontal(block_x, music_slider_y, slider_w, max(12, int(slider_h * 2)), self.ui_state["music_volume"], "music_dragging", self.ui_state)

        sfx_y = music_slider_y + max(12, int(slider_h * 2)) + int(28 * (self.screen_h / ui_helpers.REF_H))
        draw_text("Volumen Efectos", block_x, sfx_y, fsz(20), DARKGRAY)
        sfx_slider_y = sfx_y + int(28 * (self.screen_h / ui_helpers.REF_H))
        self.ui_state["sfx_volume"] = ui_helpers.slider_horizontal(block_x, sfx_slider_y, slider_w, max(12, int(slider_h * 2)), self.ui_state["sfx_volume"], "sfx_dragging", self.ui_state)

        btn_w = int(ui_dims["button_w"] * 0.6)
        btn_h = ui_dims["button_h"]
        by = self.screen_h - int(self.screen_h * 0.06) - btn_h
        gap_btn = int(12 * (self.screen_w / ui_helpers.REF_H))
        
        if ui_helpers.draw_button_left(block_x, by, btn_w, btn_h, "Aplicar", font_size=fsz(20)):
            self._apply_resolution()
        
        if ui_helpers.draw_button_left(block_x + btn_w + gap_btn, by, btn_w, btn_h, "Volver", font_size=fsz(20)):
            self.state = STATE_MAIN_MENU
            self.ui_state["res_dropdown_open"] = False

    def _apply_resolution(self) -> None:
        """Aplica la resolución seleccionada."""
        new_w, new_h = RESOLUTIONS[self.res_index]
        if new_w != self.screen_w or new_h != self.screen_h:
            self.screen_w, self.screen_h = new_w, new_h
            self.scene_w, self.scene_h = new_w, new_h
            set_window_size(self.screen_w, self.screen_h)
            
            self.scenes = self._create_scenes()
            self.map_system = MapSystem(total_scenes=len(self.scenes))
            self.player.position = self._scene_center(self.scenes[self.active_scene_index])
            self._update_camera_offset()
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)

    def _draw_play_state(self, ui_dims: dict, fsz) -> None:
        """Dibuja el estado de juego."""
        
        begin_mode_2d(self.camera)
        self.scenes[self.active_scene_index].draw()
        self.player.draw()
        end_mode_2d()

        hud_text = "En juego - [P] Menu | [I] Inventario | [M] Mapa"
        draw_text(hud_text, ui_dims["left_margin"], 10, fsz(18), DARKGRAY)

        # *** DIBUJAR INVENTARIO Y MAPA ***
        self.inventory.draw(self.screen_w, self.screen_h)
        self.map_system.draw(self.screen_w, self.screen_h, self.active_scene_index)
        # *********************************

        if self.ingame_menu_open:
            draw_rectangle(0, 0, self.screen_w, self.screen_h, Color(0, 0, 0, 160))
            
            bw = ui_dims["button_w"]
            bh = ui_dims["button_h"]
            x = ui_dims["left_margin"]
            gap = int(max(8, 12 * (self.screen_h / ui_helpers.REF_H)))
            total_h = bh * 3 + gap * 2
            cy = self.screen_h // 2 - total_h // 2
            
            if ui_helpers.draw_button_left(x, cy + 0 * (bh + gap), bw, bh, "Reanudar", font_size=fsz(20)):
                self.ingame_menu_open = False
                
            if ui_helpers.draw_button_left(x, cy + 1 * (bh + gap), bw, bh, "Menu Principal", font_size=fsz(20)):
                self.ingame_menu_open = False
                self._start_loading(self.active_scene_index, STATE_MAIN_MENU)
                
            if ui_helpers.draw_button_left(x, cy + 2 * (bh + gap), bw, bh, "Salir", font_size=fsz(20)):
                self.running = False

    def _draw_loading_overlay(self, fsz) -> None:
        """Dibuja el overlay de transición."""
        if not self.loading:
            return

        if self.trans_elapsed < FADE_TIME:
            alpha = int((self.trans_elapsed / FADE_TIME) * 255)
        elif self.trans_elapsed < FADE_TIME + HOLD_TIME:
            alpha = 255
        elif self.trans_elapsed < TRANSITION_TIME:
            t = (self.trans_elapsed - FADE_TIME - HOLD_TIME) / FADE_TIME
            alpha = int((1.0 - t) * 255)
        else:
            alpha = 0
        alpha = max(0, min(255, alpha))

        draw_rectangle(0, 0, self.screen_w, self.screen_h, Color(30, 30, 30, alpha))

        if self.loading_texture is not None:
            tex_w = self.loading_texture.width
            tex_h = self.loading_texture.height
            scale = min(self.screen_w / tex_w, self.screen_h / tex_h)
            draw_w = int(tex_w * scale)
            draw_h = int(tex_h * scale)
            draw_x = (self.screen_w - draw_w) // 2
            draw_y = (self.screen_h - draw_h) // 2
            draw_texture_ex(self.loading_texture, Vector2(draw_x, draw_y), 0.0, scale, Color(255, 255, 255, alpha))
        else:
            draw_text("Cargando...", self.screen_w // 2 - 70, self.screen_h // 2 - 10, fsz(28), Color(220, 220, 220, max(120, alpha)))