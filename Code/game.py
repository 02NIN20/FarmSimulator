# Code/game.py
from __future__ import annotations
from typing import Optional, List, Tuple, Any
from math import sin
from random import choice
from pyray import *

from player import Player
from scene import Scene
import input_handler
import ui_helpers
from inventory import Inventory
from map_system import MapSystem
from zones_geometry import zone2_alaska_polygon, zone3_ppr_polygon, zone4_michigan_polygon
from ground_spawns import SpawnManager
from save_system import SaveManager
from animal_spawns import AnimalManager   # === ANIMALES ===

# ----------------- Config -----------------

RESOLUTIONS = [
    (1920, 1080), (1600, 900), (1366, 768),
    (1280, 720), (1024, 576), (960, 540),
]

MIN_ZOOM, MAX_ZOOM = 0.35, 3.0
TRANSITION_TIME = 3.0
FADE_TIME = 0.5
HOLD_TIME = max(0.0, TRANSITION_TIME - 2.0 * FADE_TIME)
LOADING_IMAGE_PATH: str | None = None

STATE_MAIN_MENU   = "MAIN_MENU"
STATE_CONFIG      = "CONFIG"
STATE_PLAY        = "PLAY"
STATE_LOADING     = "LOADING"
STATE_SAVE_SLOTS  = "SAVE_SLOTS"

PAUSE_TAB_MAIN  = "MAIN"
PAUSE_TAB_VIDEO = "VIDEO"
PAUSE_TAB_AUDIO = "AUDIO"
PAUSE_TAB_GAME  = "GAME"


# ----------------- Reloj -----------------

class GameClock:
    SEASONS = ["Primavera", "Verano", "Otoño", "Invierno"]
    def __init__(self, seconds_per_day: float = 300.0) -> None:
        self.seconds_per_day = max(1.0, seconds_per_day)
        self.elapsed = 0.0
    def update(self, dt: float) -> None:
        self.elapsed += dt
    @property
    def day_fraction(self) -> float:
        return (self.elapsed % self.seconds_per_day) / self.seconds_per_day
    @property
    def day(self) -> int:
        return int(self.elapsed // self.seconds_per_day) + 1
    def time_hhmm(self) -> str:
        total_minutes = int(self.day_fraction * 24 * 60)
        hh = total_minutes // 60
        mm = total_minutes % 60
        return f"{hh:02d}:{mm:02d}"
    def season_name(self) -> str:
        season_len = 30
        idx = ((self.day - 1) // season_len) % len(self.SEASONS)
        return self.SEASONS[idx]


# ----------------- Juego -----------------

class Game:
    def __init__(self, initial_res_index: int) -> None:
        self.res_index = initial_res_index
        self.screen_w, self.screen_h = RESOLUTIONS[self.res_index]
        self.scene_w, self.scene_h = self.screen_w * 5, self.screen_h * 5

        init_window(self.screen_w, self.screen_h, "ASTRA - NASA Space Apps")
        set_exit_key(0)  # Evitar cerrar con ESC
        set_target_fps(60)

        self.state = STATE_MAIN_MENU
        self.running = True
        self.ingame_menu_open = False
        self.confirm_quit = False
        self.confirm_menu = False

        # transiciones
        self.loading = False
        self.trans_elapsed = 0.0
        self.target_scene: Optional[int] = None
        self.swapped = False
        self.post_load_state = STATE_PLAY
        self._keep_player_pos_on_load = False  # respeta posición al cargar

        # escenas/jugador/sistemas
        self.scenes = self._create_scenes()
        self.active_scene_index = 0
        self.player = Player(self._scene_center(self.scenes[self.active_scene_index]))

        self.inventory = Inventory(rows=4, cols=10)
        self._give_default_items()

        self.map_system = MapSystem(total_scenes=len(self.scenes))
        self.spawns = SpawnManager(self.inventory)

        # === ANIMALES === gestor de fauna
        self.animals = AnimalManager()
        self._pending_attack = False  # flag de ataque por tecla

        # hotbar
        self.hotbar_size = min(9, self.inventory.cols)
        self.hotbar_index = 0

        # cámara
        self.camera = Camera2D()
        self._update_camera_offset()
        self.camera.target = Vector2(self.player.position.x, self.player.position.y)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        # UI
        self.ui_state = {
            "master_volume": 1.0, "music_volume": 0.8, "sfx_volume": 0.9,
            "music_dragging": False, "sfx_dragging": False, "master_dragging": False,
            "brightness": 0.5, "brightness_dragging": False, "show_grid": True,
            "show_fps": False, "res_dropdown_open": False, "pause_tab": PAUSE_TAB_MAIN,
        }
        self._apply_grid_visibility_to_scenes()

        # reloj
        self.clock = GameClock(seconds_per_day=300.0)

        # assets
        self.loading_texture: Optional[Texture2D] = None
        self.spring_texture: Optional[Texture2D] = None  # <--- portada Primavera
        self._load_assets()

        # Menú principal estacional
        self.main_menu = {"t": 0.0, "selected": 0, "credits_open": False, "theme": "Primavera", "particles": []}
        self._init_main_menu_theme()

        # Guardados
        self.save_mgr = SaveManager("saves")
        self.current_save_id: str | None = None
        self.current_save_name: str = ""
        self._rename_slot_id: str | None = None
        self._rename_buffer: str = ""

        # Modal “nueva partida”
        self._newgame_modal_open = False
        self._newgame_name = ""

        # cabañas en 2,3,4
        self.cabins: dict[int, list[Rectangle]] = {}
        self._setup_cabins()

    # ---------- helpers ----------
    def _give_default_items(self) -> None:
        try:
            self.inventory.clear_all()
        except Exception:
            try:
                for s in self.inventory.slots:
                    s.clear()
            except Exception:
                pass
        self.inventory.add_item("seed_corn", 10)
        self.inventory.add_item("seed_wheat", 6)
        self.inventory.add_item("water", 20)
        self.inventory.add_item("fertilizer", 8)

    def _apply_grid_visibility_to_scenes(self) -> None:
        show = bool(self.ui_state.get("show_grid", True))
        for s in self.scenes:
            s.grid_enabled = show

    def _update_camera_offset(self) -> None:
        self.camera.offset = Vector2(self.screen_w / 2, self.screen_h / 2)

    def _scene_center(self, scene: Scene) -> Vector2:
        return Vector2(scene.size.x * 0.5, scene.size.y * 0.5)

    def _make_scene(self, scene_id: int, land: Color) -> Scene:
        size = Vector2(self.scene_w, self.scene_h)
        spawn = Vector2(self.scene_w * 0.5, self.scene_h * 0.5)
        return Scene(scene_id, size, land, spawn, land_color=land)

    def _clamp_camera_to_scene(self) -> None:
        scene = self.scenes[self.active_scene_index]
        half_w = (self.screen_w * 0.5) / max(0.001, self.camera.zoom)
        half_h = (self.screen_h * 0.5) / max(0.001, self.camera.zoom)
        tx = max(half_w, min(scene.size.x - half_w, self.camera.target.x))
        ty = max(half_h, min(scene.size.y - half_h, self.camera.target.y))
        self.camera.target = Vector2(tx, ty)

    def _fit_font(self, text: str, max_width: int, base: int, min_size: int = 14) -> int:
        size = base
        while size > min_size and measure_text(text, size) > max_width:
            size -= 1
        return max(min_size, size)

    # ---------- escenas ----------
    def _create_scenes(self) -> list[Scene]:
        LOCAL_LAND   = Color(128, 178, 112, 255)
        ALASKA_LAND  = Color(100, 142, 120, 255)
        PPR_LAND     = Color(160, 175,  90, 255)
        MICH_LAND    = Color( 92, 150, 110, 255)

        s1 = self._make_scene(1, LOCAL_LAND)

        s2 = Scene(2, Vector2(self.scene_w, self.scene_h), ALASKA_LAND,
                   Vector2(self.scene_w*0.5, self.scene_h*0.5),
                   grid_cell_size=48, grid_enabled=True,
                   polygon_norm=zone2_alaska_polygon(), land_color=ALASKA_LAND)
        s3 = Scene(3, Vector2(self.scene_w, self.scene_h), PPR_LAND,
                   Vector2(self.scene_w*0.5, self.scene_h*0.5),
                   grid_cell_size=48, grid_enabled=True,
                   polygon_norm=zone3_ppr_polygon(), land_color=PPR_LAND)
        s4 = Scene(4, Vector2(self.scene_w, self.scene_h), MICH_LAND,
                   Vector2(self.scene_w*0.5, self.scene_h*0.5),
                   grid_cell_size=48, grid_enabled=True,
                   polygon_norm=zone4_michigan_polygon(), land_color=MICH_LAND)
        return [s1, s2, s3, s4]

    def _load_assets(self) -> None:
        if LOADING_IMAGE_PATH is not None:
            try:
                self.loading_texture = load_texture(LOADING_IMAGE_PATH)
            except Exception:
                self.loading_texture = None

        # --- Portada personalizada para Primavera ---
        try:
            # coloca tu imagen en assets/apertura.png
            self.spring_texture = load_texture("assets/apertura.png")
        except Exception:
            self.spring_texture = None

    def _unload_assets(self) -> None:
        if self.loading_texture is not None:
            unload_texture(self.loading_texture)
            self.loading_texture = None
        if self.spring_texture is not None:
            unload_texture(self.spring_texture)
            self.spring_texture = None

    # ---------- loop ----------
    def run(self) -> None:
        while self.running and not window_should_close():
            dt = get_frame_time()
            self._handle_input()
            self._update(dt)
            self._draw()
        self._unload_assets()
        close_window()

    # ---------- input ----------
    def _handle_input(self) -> None:
        # Menú principal
        if self.state == STATE_MAIN_MENU:
            labels = ["Jugar", "Configuración", "Créditos", "Salir"]
            if is_key_pressed(KEY_UP):
                self.main_menu["selected"] = (self.main_menu["selected"] - 1) % len(labels)
            if is_key_pressed(KEY_DOWN):
                self.main_menu["selected"] = (self.main_menu["selected"] + 1) % len(labels)
            if is_key_pressed(KEY_ENTER) or is_key_pressed(KEY_KP_ENTER):
                self._activate_main_menu_item(labels[self.main_menu["selected"]])
            if is_key_pressed(KEY_T):
                self._init_main_menu_theme()

        # Selector de partidas
        if self.state == STATE_SAVE_SLOTS:
            if is_key_pressed(KEY_ESCAPE):
                if self._rename_slot_id:
                    self._rename_slot_id = None
                elif self._newgame_modal_open:
                    self._newgame_modal_open = False
                else:
                    self.state = STATE_MAIN_MENU

        # En juego: toggles
        if self.state == STATE_PLAY and not self.loading:
            if is_key_pressed(KEY_I):
                if self.map_system.is_open:
                    self.map_system.is_open = False
                self.inventory.toggle()
            if is_key_pressed(KEY_M):
                if self.inventory.is_open:
                    self.inventory.is_open = False
                self.map_system.toggle()

        # ESC
        if is_key_pressed(KEY_ESCAPE):
            if self.state == STATE_CONFIG:
                self.state = STATE_MAIN_MENU
                self.ui_state["res_dropdown_open"] = False
            elif self.state == STATE_PLAY:
                if self.inventory.is_open:
                    self.inventory.is_open = False
                elif self.map_system.is_open:
                    self.map_system.is_open = False
                else:
                    self.ingame_menu_open = not self.ingame_menu_open
                    self.confirm_quit = False
                    self.confirm_menu = False
                    self.ui_state["pause_tab"] = PAUSE_TAB_MAIN

        # Dormir/Guardar con E en cabaña
        if (self.state == STATE_PLAY and not self.loading and
            not self.ingame_menu_open and not self.inventory.is_open and not self.map_system.is_open):
            if is_key_pressed(KEY_E) and self._player_near_cabin():
                self._sleep_and_save()

        # === ANIMALES ===: ataque jugador (tecla ESPACIO)
        if (self.state == STATE_PLAY and not self.loading and
            not self.ingame_menu_open and not self.inventory.is_open and not self.map_system.is_open):
            self._pending_attack = is_key_pressed(KEY_SPACE)

        # Mapa: click viajar
        if (self.state == STATE_PLAY and not self.loading and self.map_system.is_open and not self.ingame_menu_open):
            if is_mouse_button_pressed(MOUSE_LEFT_BUTTON):
                next_idx = -1
                try:
                    next_idx = self.map_system.handle_click(self.screen_w, self.screen_h)
                except Exception:
                    next_idx = -1
                if (isinstance(next_idx, int) and 0 <= next_idx < len(self.scenes)
                        and next_idx != self.active_scene_index):
                    self._start_loading(next_idx, STATE_PLAY, keep_player_pos=False)
                    self.map_system.is_open = False
                    self.inventory.is_open  = False
                    self.ingame_menu_open   = False

        # Hotbar: scroll y 1..9
        if self.state == STATE_PLAY and not self.loading:
            wheel = get_mouse_wheel_move()
            if wheel > 0.0:
                self.hotbar_index = (self.hotbar_index - 1) % self.hotbar_size
            elif wheel < 0.0:
                self.hotbar_index = (self.hotbar_index + 1) % self.hotbar_size
            if is_key_pressed(KEY_ONE):   self.hotbar_index = 0
            if is_key_pressed(KEY_TWO):   self.hotbar_index = min(1, self.hotbar_size - 1)
            if is_key_pressed(KEY_THREE): self.hotbar_index = min(2, self.hotbar_size - 1)
            if is_key_pressed(KEY_FOUR):  self.hotbar_index = min(3, self.hotbar_size - 1)
            if is_key_pressed(KEY_FIVE):  self.hotbar_index = min(4, self.hotbar_size - 1)
            if is_key_pressed(KEY_SIX):   self.hotbar_index = min(5, self.hotbar_size - 1)
            if is_key_pressed(KEY_SEVEN): self.hotbar_index = min(6, self.hotbar_size - 1)
            if is_key_pressed(KEY_EIGHT): self.hotbar_index = min(7, self.hotbar_size - 1)
            if is_key_pressed(KEY_NINE):  self.hotbar_index = min(8, self.hotbar_size - 1)

    # ---------- update ----------
    def _update(self, dt: float) -> None:
        if self.state == STATE_MAIN_MENU:
            self._update_menu_fx(dt)

        if self.loading:
            self.trans_elapsed += dt
            if (not self.swapped) and (self.trans_elapsed >= FADE_TIME):
                if self.target_scene is not None:
                    self.active_scene_index = self.target_scene
                    if not self._keep_player_pos_on_load:
                        self.player.position = self._scene_center(self.scenes[self.active_scene_index])
                        self.player.destination = self.player.position
                    self.camera.target = Vector2(self.player.position.x, self.player.position.y)
                    self._clamp_camera_to_scene()
                    try:
                        poly = getattr(self.scenes[self.active_scene_index], "polygon_world", None)
                    except Exception:
                        poly = None
                    self.spawns.on_enter_scene(self.active_scene_index, self.scenes[self.active_scene_index].size, poly)
                    # === ANIMALES ===: spawns al entrar
                    try:
                        self.animals.on_enter_scene(self.active_scene_index, self.scenes[self.active_scene_index].size, poly)
                    except Exception:
                        pass
                self.swapped = True
            if self.trans_elapsed >= TRANSITION_TIME:
                self._end_loading()
                self.state = self.post_load_state

        # Lógica en juego
        if (self.state == STATE_PLAY and not self.loading and
            not self.ingame_menu_open and not self.inventory.is_open and not self.map_system.is_open):
            mouse_world = get_screen_to_world_2d(get_mouse_position(), self.camera)
            p_input = input_handler.get_player_input(self.player.position, self.player.destination, mouse_world)
            old_x, old_y = self.player.position.x, self.player.position.y
            self.player.update(p_input, dt)

            scene = self.scenes[self.active_scene_index]
            cm = getattr(scene, "collision_map", None)
            if cm is not None:
                size = float(self.player.size)
                half = size * 0.5

                def collides_at(px: float, py: float) -> bool:
                    return cm.rect_collides(px - half, py - half, size, size, scene.grid_cell_size, scene.grid_cell_size)

                new_x, new_y = self.player.position.x, self.player.position.y
                test_x, test_y = new_x, new_y
                if collides_at(test_x, old_y):
                    test_x = old_x
                if collides_at(test_x, test_y):
                    if collides_at(test_x, old_y):
                        test_y = old_y
                    else:
                        if collides_at(old_x, new_y):
                            test_y = old_y

                # cabañas
                if self._collides_cabin(test_x, test_y):
                    if not self._collides_cabin(test_x, old_y):
                        test_y = old_y
                    elif not self._collides_cabin(old_x, test_y):
                        test_x = old_x
                    else:
                        test_x, test_y = old_x, old_y

                self.player.position.x, self.player.position.y = test_x, test_y
                if collides_at(self.player.destination.x, self.player.destination.y):
                    self.player.destination = Vector2(self.player.position.x, self.player.position.y)

            # === ANIMALES ===: actualizar IA y aplicar daño recibido
            try:
                damages = self.animals.update(self.active_scene_index, dt, self.player.position)
                for dmg in damages:
                    if hasattr(self.player, "apply_damage"):
                        self.player.apply_damage(dmg)
                    else:
                        # fallback mínimo si Player no tiene apply_damage
                        self.player.hp = max(0.0, getattr(self.player, "hp", 100.0) - float(dmg))
            except Exception:
                pass

            # === ANIMALES ===: ataque del jugador si pulsó ESPACIO
            if self._pending_attack:
                did_attack = False
                if hasattr(self.player, "try_attack"):
                    try:
                        did_attack = bool(self.player.try_attack(dt))
                    except Exception:
                        did_attack = False
                if not did_attack:
                    # Fallback si Player no implementa try_attack: consume STA y aplica daño
                    cost = 16.0
                    if getattr(self.player, "stamina", 0.0) >= cost:
                        self.player.stamina = max(0.0, self.player.stamina - cost)
                        did_attack = True
                if did_attack:
                    # radio y daño por defecto si Player no los trae
                    radius = float(getattr(self.player, "attack_radius", 40.0))
                    damage = float(getattr(self.player, "attack_damage", 22.0))
                    try:
                        self.animals.damage_in_radius(self.active_scene_index, self.player.position, radius, damage)
                    except Exception:
                        pass

            # zoom y cámara
            if is_key_down(KEY_EQUAL) or is_key_down(KEY_KP_ADD):
                self.camera.zoom += 1.0 * dt
            if is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT):
                self.camera.zoom -= 1.0 * dt
            self.camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.camera.zoom))
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)
            self._clamp_camera_to_scene()

        self.clock.update(dt)

    # ---------- transiciones ----------
    def _start_loading(self, target_scene_index: int, next_state: str, keep_player_pos: bool = False) -> None:
        self.loading = True
        self.trans_elapsed = 0.0
        self.target_scene = target_scene_index
        self.swapped = False
        self.post_load_state = next_state
        self._keep_player_pos_on_load = bool(keep_player_pos)
        self.state = STATE_LOADING

    def _end_loading(self) -> None:
        self.loading = False
        self.target_scene = None
        self.swapped = False  # <- aquí estaba la indentación rota
        self.trans_elapsed = 0.0
        self._keep_player_pos_on_load = False

    # ---------- draw ----------
    def _draw(self) -> None:
        begin_drawing()
        clear_background(RAYWHITE)
        ui = ui_helpers.calculate_ui_dimensions(self.screen_w, self.screen_h)
        fsz = lambda base: ui_helpers.calc_font(self.screen_h, base)

        if self.state == STATE_MAIN_MENU:
            self._draw_main_menu(ui, fsz)
        elif self.state == STATE_CONFIG:
            self._draw_config(ui, fsz)
        elif self.state == STATE_SAVE_SLOTS:
            self._draw_save_slots(fsz)
        elif self.state in (STATE_PLAY, STATE_LOADING):
            self._draw_play_state(ui, fsz)
            self._draw_loading_overlay(fsz)
        else:
            draw_text("Estado desconocido", 10, 10, fsz(22), RED)

        end_drawing()

    # ---------- Menú principal ----------
    def _draw_main_menu(self, ui_dims: dict, fsz) -> None:
        self._draw_menu_background()
        t = float(self.main_menu.get("t", 0.0))
        base_fs = fsz(64)
        pulse = 1.0 + 0.02 * sin(t * 2.1)
        fs = int(base_fs * pulse)
        title = "ASTRA"
        tx = (self.screen_w - measure_text(title, fs)) // 2
        ty = int(self.screen_h * 0.12)
        draw_text(title, tx + 2, ty + 2, fs, Color(0, 0, 0, 90))
        draw_text(title, tx, ty, fs, Color(25, 102, 204, 255))

        labels = ["Jugar", "Configuración", "Créditos", "Salir"]
        bw = int(min(self.screen_w * 0.35, 420))
        bh = max(42, int(self.screen_h * 0.07 * 0.6))
        gap = int(bh * 0.35)
        start_y = max(ty + fs + int(self.screen_h * 0.08), int(self.screen_h * 0.46))
        x = (self.screen_w - bw) // 2
        for i, text in enumerate(labels):
            y = start_y + i * (bh + gap)
            hovered, clicked = self._menu_button(x, y, bw, bh, text, fsz(24), i == self.main_menu["selected"])
            if hovered:
                self.main_menu["selected"] = i
            if clicked:
                self._activate_main_menu_item(text)

        tip = "↑/↓ para navegar   •   Enter para aceptar   •   T cambia fondo"
        fs_tip = fsz(16)
        draw_text(tip, (self.screen_w - measure_text(tip, fs_tip)) // 2, self.screen_h - fs_tip - 12, fs_tip, Color(40, 40, 40, 200))

        if self.main_menu.get("credits_open", False):
            self._draw_credits_overlay(fsz)

    def _activate_main_menu_item(self, label: str) -> None:
        if label == "Jugar":
            self.state = STATE_SAVE_SLOTS
        elif label == "Configuración":
            self.state = STATE_CONFIG
            self.ui_state["res_dropdown_open"] = False
        elif label == "Créditos":
            self.main_menu["credits_open"] = True
        elif label == "Salir":
            self.running = False

    # ---- Tema estacional (fondos animados) ----
    def _init_main_menu_theme(self) -> None:
        theme = choice(["Primavera", "Verano", "Otoño", "Invierno"])
        self.main_menu["theme"] = theme
        w, h = self.screen_w, self.screen_h
        particles = []
        if theme == "Primavera":
            for _ in range(60):
                particles.append({"shape": "dot","x": float(get_random_value(0, w)),"y": float(get_random_value(0, h)),
                                  "vx": (get_random_value(-6, 6)/10.0),"vy": (get_random_value(5, 14)/10.0),
                                  "r": 1.6+(get_random_value(0,10)/10.0),"a": get_random_value(80,130),
                                  "phase": get_random_value(0,628)/100.0})
        elif theme == "Verano":
            for _ in range(50):
                particles.append({"shape": "spark","x": float(get_random_value(0, w)),"y": float(get_random_value(0, h)),
                                  "vx": (get_random_value(-4, 4)/10.0),"vy": (get_random_value(2, 10)/10.0),
                                  "r": 1.5+(get_random_value(0,12)/10.0),"a": get_random_value(70,140)})
        elif theme == "Otoño":
            for _ in range(45):
                particles.append({"shape": "leaf","x": float(get_random_value(0, w)),"y": float(get_random_value(-h//2, h)),
                                  "vx": (get_random_value(-8, 8)/10.0),"vy": (get_random_value(8, 18)/10.0),
                                  "w": 10+get_random_value(0,6),"h": 4+get_random_value(0,4),
                                  "rot": float(get_random_value(0,360)),"rot_speed": (get_random_value(-50,50)/10.0),
                                  "a": get_random_value(120,200),"phase": get_random_value(0,628)/100.0})
        else:
            for _ in range(70):
                particles.append({"shape": "snow","x": float(get_random_value(0, w)),"y": float(get_random_value(-h//2, h)),
                                  "vx": (get_random_value(-7, 7)/10.0),"vy": (get_random_value(9, 20)/10.0),
                                  "r": 1.8+(get_random_value(0,15)/10.0),"a": get_random_value(160,230),
                                  "phase": get_random_value(0,628)/100.0})
        self.main_menu["particles"] = particles

    def _update_menu_fx(self, dt: float) -> None:
        m = self.main_menu
        m["t"] += dt
        theme = m.get("theme", "Primavera")
        w, h = self.screen_w, self.screen_h
        for p in m["particles"]:
            if theme == "Primavera":
                p["x"] += (p["vx"] + 0.5 * sin(m["t"] * 1.2 + p["phase"])) * 60.0 * dt
                p["y"] -= p["vy"] * 60.0 * dt
                if p["y"] < -20:
                    p["y"] = h + 20
                    p["x"] = float(get_random_value(0, w))
            elif theme == "Verano":
                p["x"] += p["vx"] * 60.0 * dt
                p["y"] += p["vy"] * 60.0 * dt
                if p["y"] > h + 20:
                    p["y"] = -20
                    p["x"] = float(get_random_value(0, w))
            elif theme == "Otoño":
                p["rot"] += p["rot_speed"] * dt
                sway = 0.8 * sin(m["t"] * 1.6 + p["phase"])
                p["x"] += (p["vx"] + sway) * 60.0 * dt
                p["y"] += p["vy"] * 60.0 * dt
                if p["y"] > h + 20:
                    p["y"] = -20
                    p["x"] = float(get_random_value(0, w))
            else:
                sway = 0.9 * sin(m["t"] * 1.4 + p["phase"])
                p["x"] += (p["vx"] + sway) * 60.0 * dt
                p["y"] += p["vy"] * 60.0 * dt
                if p["y"] > h + 20:
                    p["y"] = -20
                    p["x"] = float(get_random_value(0, w))

    def _draw_menu_background(self) -> None:
        theme = self.main_menu.get("theme", "Primavera")

        # --- Fondo según tema ---
        if theme == "Primavera":
            # Si hay textura personalizada, usarla; si no, fallback al gradiente original
            if self.spring_texture is not None:
                tex = self.spring_texture
                scale = min(self.screen_w / tex.width, self.screen_h / tex.height)
                draw_w = int(tex.width * scale)
                draw_h = int(tex.height * scale)
                draw_x = (self.screen_w - draw_w) // 2
                draw_y = (self.screen_h - draw_h) // 2
                draw_texture_ex(tex, Vector2(draw_x, draw_y), 0.0, scale, WHITE)
            else:
                draw_rectangle_gradient_v(0, 0, self.screen_w, self.screen_h, Color(224,238,224,255), Color(205,228,205,255))
            grid_c = Color(80,120,90,25)
        elif theme == "Verano":
            draw_rectangle_gradient_v(0, 0, self.screen_w, self.screen_h, Color(210,232,252,255), Color(158,203,251,255))
            draw_circle(self.screen_w - 150, 120, 90, Color(255, 240, 180, 40))
            grid_c = Color(60, 90, 130, 22)
        elif theme == "Otoño":
            draw_rectangle_gradient_v(0, 0, self.screen_w, self.screen_h, Color(250,230,200,255), Color(224,186,120,255))
            grid_c = Color(120,70,30,28)
        else:
            draw_rectangle_gradient_v(0, 0, self.screen_w, self.screen_h, Color(226,236,246,255), Color(200,218,238,255))
            grid_c = Color(60,90,120,25)

        # Rejilla sutil superpuesta
        cell = max(48, int(self.screen_h * 0.08))
        for x in range(0, self.screen_w, cell):
            draw_line(x, 0, x, self.screen_h, grid_c)
        for y in range(0, self.screen_h, cell):
            draw_line(0, y, self.screen_w, y, grid_c)

        # Partículas encima del fondo
        begin_blend_mode(BLEND_ALPHA)
        if theme in ("Primavera", "Invierno"):
            for p in self.main_menu["particles"]:
                c = Color(120,170,120,int(p["a"])) if theme=="Primavera" else Color(255,255,255,int(p["a"]))
                draw_circle(int(p["x"]), int(p["y"]), float(p["r"]), c)
        elif theme == "Verano":
            for p in self.main_menu["particles"]:
                draw_circle(int(p["x"]), int(p["y"]), float(p["r"]), Color(255,255,255,int(p["a"])))
            begin_blend_mode(BLEND_ADDITIVE)
            draw_circle(self.screen_w - 130, 110, 110, Color(255,230,160,26))
            draw_circle(self.screen_w - 130, 110, 180, Color(255,230,160,18))
            end_blend_mode()
        else:
            for p in self.main_menu["particles"]:
                leaf_col = [Color(190,120,40,int(p["a"])), Color(215,150,50,int(p["a"])), Color(175,95,35,int(p["a"]))][(int(p["x"] + p["y"]) // 50) % 3]
                rect = Rectangle(int(p["x"]), int(p["y"]), int(p["w"]), int(p["h"]))
                origin = Vector2(p["w"]/2, p["h"]/2)
                draw_rectangle_pro(rect, origin, float(p["rot"]), leaf_col)
                draw_rectangle_lines_ex(rect, 1, Color(0, 0, 0, 40))
        end_blend_mode()

    def _menu_button(self, x: int, y: int, w: int, h: int, label: str, fs: int, selected: bool):
        mx, my = get_mouse_x(), get_mouse_y()
        hovered = (x <= mx <= x + w) and (y <= my <= y + h)
        clicked = hovered and is_mouse_button_pressed(MOUSE_LEFT_BUTTON)
        bg  = Color(60,60,60,220) if not (hovered or selected) else Color(85,85,90,240)
        self._draw_panel(x, y, w, h, bg, Color(0,0,0,210), radius=0.18)
        tx = x + (w - measure_text(label, fs)) // 2
        ty = y + (h - fs) // 2
        self._draw_text_shadow(label, tx, ty, fs, Color(240, 240, 240, 255))
        return hovered, clicked

    def _draw_credits_overlay(self, fsz) -> None:
        draw_rectangle(0, 0, self.screen_w, self.screen_h, Color(0, 0, 0, 150))
        w = int(self.screen_w * 0.55)
        h = int(self.screen_h * 0.55)
        x = (self.screen_w - w)//2
        y = (self.screen_h - h)//2
        self._draw_panel(x, y, w, h, Color(250, 250, 250, 255), Color(60, 60, 60, 230), radius=0.08)
        draw_text("CRÉDITOS", x + 16, y + 14, fsz(28), BLACK)
        fs = fsz(18)
        lines = [
            "Astra — NASA Space Apps Challenge", "",
            "Diseño y desarrollo: Equipo Astra",
            "Arte y UI: Denisse (personaje), mapas y HUD)",
            "Tecnologías: Python + raylib (pyray)",
        ]
        ty = y + 64
        for ln in lines:
            draw_text(ln, x + 16, ty, fs, BLACK)
            ty += fs + 6
        bw, bh = 140, 40
        bx = x + w - bw - 16
        by = y + h - bh - 16
        _, clicked = self._menu_button(bx, by, bw, bh, "Cerrar", fsz(20), False)
        if clicked:
            self.main_menu["credits_open"] = False

    # ---------- Config ----------
    def _draw_config(self, ui_dims: dict, fsz) -> None:
        draw_text("CONFIGURACIÓN", ui_dims["left_margin"], int(self.screen_h * 0.12), fsz(32), BLACK)
        block_x = ui_dims["left_margin"]
        block_y = int(self.screen_h * 0.22)
        slider_w = ui_dims["slider_w"]
        slider_h = ui_dims["slider_h"]
        gap_y = int(self.screen_h * 0.06)

        draw_text("Música", block_x, block_y - fsz(18), fsz(18), BLACK)
        self.ui_state["music_volume"] = ui_helpers.slider_horizontal(block_x, block_y, slider_w, slider_h, self.ui_state["music_volume"], "music_dragging", self.ui_state)

        sfx_y = block_y + gap_y
        draw_text("SFX", block_x, sfx_y - fsz(18), fsz(18), BLACK)
        self.ui_state["sfx_volume"] = ui_helpers.slider_horizontal(block_x, sfx_y, slider_w, slider_h, self.ui_state["sfx_volume"], "sfx_dragging", self.ui_state)

        drop_y = sfx_y + gap_y
        draw_text("Resolución", block_x, drop_y - fsz(18), fsz(18), BLACK)
        drop_w = int(slider_w * 0.9)
        drop_h = max(28, ui_dims["button_h"])
        drop_label = f"{RESOLUTIONS[self.res_index][0]}x{RESOLUTIONS[self.res_index][1]}"
        _, clicked = ui_helpers.button_left_rect(block_x, drop_y, drop_w, drop_h, drop_label, fsz(18))
        if clicked:
            self.ui_state["res_dropdown_open"] = not self.ui_state["res_dropdown_open"]
        if self.ui_state["res_dropdown_open"]:
            opt_h = drop_h
            for i in range(len(RESOLUTIONS)):
                oy = drop_y + (i + 1) * (opt_h + 4)
                txt = f"{RESOLUTIONS[i][0]}x{RESOLUTIONS[i][1]}"
                _, opt_clicked = ui_helpers.button_left_rect(block_x, oy, drop_w, opt_h, txt, fsz(18))
                if opt_clicked:
                    self.res_index = i
                    self.ui_state["res_dropdown_open"] = False
                    break

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
        new_w, new_h = RESOLUTIONS[self.res_index]
        if new_w != self.screen_w or new_h != self.screen_h:
            self.screen_w, self.screen_h = new_w, new_h
            self.scene_w, self.scene_h = new_w * 5, new_h * 5
            set_window_size(self.screen_w, self.screen_h)
            self.scenes = self._create_scenes()
            self.map_system = MapSystem(total_scenes=len(self.scenes))
            self._apply_grid_visibility_to_scenes()
            self.player.position = self._scene_center(self.scenes[self.active_scene_index])
            self._update_camera_offset()
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)
            self._clamp_camera_to_scene()
            self._setup_cabins()

    # ---------- Juego ----------
    def _draw_play_state(self, ui_dims: dict, fsz) -> None:
        begin_mode_2d(self.camera)
        self.scenes[self.active_scene_index].draw()
        self._draw_cabins_world()
        # === ANIMALES === dibujar fauna en el mundo
        try:
            self.animals.draw(self.active_scene_index)
        except Exception:
            pass
        self.spawns.draw(self.active_scene_index)
        self.player.draw()
        self.spawns.update(self.active_scene_index, self.player.position)
        end_mode_2d()

        self._apply_brightness_overlay()
        self._draw_hud(fsz)
        self.inventory.draw(self.screen_w, self.screen_h)
        self.map_system.draw(self.screen_w, self.screen_h, self.active_scene_index)

        if self.ingame_menu_open:
            self._draw_pause_menu(ui_dims, fsz)

        self._draw_sleep_prompt(fsz)

    def _color_scale(self, c: Color, factor: float) -> Color:
        return Color(int(max(0, min(255, c.r * factor))),
                     int(max(0, min(255, c.g * factor))),
                     int(max(0, min(255, c.b * factor))),
                     c.a)

    def _draw_text_shadow(self, text: str, x: int, y: int, fs: int, fg: Color) -> None:
        draw_text(text, x + 1, y + 1, fs, Color(0, 0, 0, 120))
        draw_text(text, x, y, fs, fg)

    def _draw_panel(self, x: int, y: int, w: int, h: int, fill: Color, border: Color, radius: float = 0.2) -> None:
        draw_rectangle(x + 2, y + 2, w, h, Color(0, 0, 0, 60))
        try:
            draw_rectangle_rounded(Rectangle(x, y, w, h), radius, 8, fill)
            draw_rectangle_rounded_lines(Rectangle(x, y, w, h), radius, 8, 2, border)
        except Exception:
            draw_rectangle(x, y, w, h, fill)
            draw_rectangle_lines(x, y, w, h, border)

    def _draw_bar(self, x: int, y: int, w: int, h: int, value: float, max_value: float, color_fill: Color, label: str) -> None:
        ratio = 0.0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
        back = Color(30, 30, 30, 170)
        back_border = Color(15, 15, 15, 220)
        fill_dark = self._color_scale(color_fill, 0.88)
        self._draw_panel(x, y, w, h, back, back_border, radius=0.35)
        inner_w = int((w - 6) * ratio)
        if inner_w > 0:
            self._draw_panel(x + 3, y + 3, inner_w, h - 6, color_fill, self._color_scale(fill_dark, 0.9), radius=0.35)
        fs = max(14, h - 8)
        txt = f"{label} {int(value)}/{int(max_value)}"
        tx = x + (w - measure_text(txt, fs)) // 2
        ty = y + (h - fs) // 2
        self._draw_text_shadow(txt, tx, ty, fs, Color(245, 245, 245, 240))

    # ---------- HOTBAR ----------
    def _palette_for_item(self, item_id: str) -> Color:
        palette = [
            Color(240, 210, 80, 255), Color(200, 225, 255, 255), Color(170, 210, 110, 255),
            Color(220, 170, 90, 255), Color(170, 140, 100, 255), Color(210, 110, 110, 255),
            Color(120, 160, 220, 255), Color(90, 180, 140, 255), Color(200, 200, 200, 255),
        ]
        h = sum(ord(c) for c in (item_id or ""))
        return palette[h % len(palette)]

    def _slot_item_info(self, slot: Any) -> Optional[Tuple[str, int]]:
        if slot is None:
            return None
        try:
            if hasattr(slot, "is_empty") and callable(slot.is_empty) and slot.is_empty():
                return None
        except Exception:
            pass
        try:
            it = getattr(slot, "item", None)
            if it is not None:
                it_id = getattr(it, "id", getattr(it, "name", None))
                qty = int(getattr(slot, "quantity", getattr(slot, "qty", getattr(slot, "count", 1))))
                if it_id:
                    return (str(it_id), qty)
        except Exception:
            pass
        try:
            it_id = getattr(slot, "id", None)
            if it_id:
                qty = int(getattr(slot, "quantity", getattr(slot, "qty", getattr(slot, "count", 1))))
                return (str(it_id), qty)
        except Exception:
            pass
        if isinstance(slot, dict):
            it_id = slot.get("id") or slot.get("item_id")
            if it_id:
                qty = int(slot.get("quantity", slot.get("qty", slot.get("count", 1))))
                return (str(it_id), qty)
        return None

    def _first_row_slots(self) -> List[Any]:
        out = []
        try:
            cols = self.inventory.cols
            if hasattr(self.inventory, "get_slot") and callable(self.inventory.get_slot):
                for c in range(cols):
                    out.append(self.inventory.get_slot(0, c))
            else:
                slots = getattr(self.inventory, "slots", [])
                for c in range(cols):
                    out.append(slots[c] if c < len(slots) else None)
        except Exception:
            out = [None] * self.hotbar_size
        return out

    def _draw_hotbar_right(self) -> None:
        slot_size = min(60, int(self.screen_h * 0.068))
        pad = max(6, int(slot_size * 0.12))
        total_h = self.hotbar_size * (slot_size + pad) - pad
        x = self.screen_w - slot_size - 20
        y = (self.screen_h - total_h) // 2
        self._draw_panel(x - 10, y - 10, slot_size + 20, total_h + 20, Color(20, 20, 20, 130), Color(0, 0, 0, 180), radius=0.2)

        first_row = self._first_row_slots()
        for i in range(self.hotbar_size):
            sx, sy = x, y + i * (slot_size + pad)
            self._draw_panel(sx, sy, slot_size, slot_size, Color(60,58,55,210), Color(0,0,0,200), radius=0.2)

            info = None
            try:
                slot = first_row[i] if i < len(first_row) else None
                info = self._slot_item_info(slot)
            except Exception:
                info = None

            if info:
                item_id, qty = info
                inner = int(slot_size * 0.78)
                ix = sx + (slot_size - inner) // 2
                iy = sy + (slot_size - inner) // 2
                col = self._palette_for_item(item_id)
                self._draw_panel(ix, iy, inner, inner, col, self._color_scale(col, 0.7), radius=0.18)
                nf = max(12, int(slot_size * 0.26))
                qtxt = str(qty)
                draw_text(qtxt, sx + slot_size - measure_text(qtxt, nf) - 6, sy + slot_size - nf - 4, nf, RAYWHITE)

            if i == self.hotbar_index:
                draw_rectangle_lines(sx - 3, sy - 3, slot_size + 6, slot_size + 6, Color(255, 220, 120, 255))
                draw_rectangle_lines(sx - 1, sy - 1, slot_size + 2, slot_size + 2, Color(255, 255, 255, 90))

            num_text = str(i + 1)
            nf = max(12, int(slot_size * 0.23))
            self._draw_text_shadow(num_text, sx + slot_size - measure_text(num_text, nf) - 6, sy + 4, nf, Color(240, 240, 240, 230))

    def _current_location_name(self) -> str:
        try:
            return self.map_system.scene_names[self.active_scene_index]
        except Exception:
            return f"Escenario {self.active_scene_index + 1}"

    def _draw_hud(self, fsz) -> None:
        margin = 12
        panel_x = margin
        panel_y = margin
        panel_w = self.screen_w - margin * 2
        top_text = f"{self.clock.time_hhmm()}  |  Día {self.clock.day}  |  {self.clock.season_name()}  |  {self._current_location_name()}"
        fs_fit = self._fit_font(top_text, panel_w - 28, fsz(22), 14)
        panel_h = fs_fit + 18
        self._draw_panel(panel_x, panel_y, panel_w, panel_h, Color(240, 240, 240, 170), Color(30, 30, 30, 200), radius=0.18)
        text_x = panel_x + (panel_w - measure_text(top_text, fs_fit)) // 2
        self._draw_text_shadow(top_text, text_x, panel_y + 9, fs_fit, Color(20, 20, 20, 240))

        bar_w = min(int(self.screen_w * 0.32), 460)
        bar_h = max(20, int(self.screen_h * 0.026))
        bars_x = margin
        first_bar_y = panel_y + panel_h + 10
        self._draw_bar(bars_x, first_bar_y, bar_w, bar_h, getattr(self.player,"hp",100.0), getattr(self.player,"max_hp",100.0), Color(210,70,70,255), "HP")
        self._draw_bar(bars_x, first_bar_y + bar_h + 8, bar_w, bar_h, self.player.stamina, self.player.max_stamina, Color(80,180,100,255), "STA")

        if self.ui_state.get("show_fps", False):
            fps_txt = f"{get_fps()} FPS"
            fs = max(14, int(self.screen_h * 0.022))
            draw_text(fps_txt, self.screen_w - measure_text(fps_txt, fs) - 10, 10, fs, BLACK)

        self._draw_hotbar_right()

    def _apply_brightness_overlay(self) -> None:
        b = float(self.ui_state.get("brightness", 0.5))
        b = max(0.0, min(1.0, b))
        if abs(b - 0.5) < 0.01:
            return
        intensity = abs(b - 0.5) * 2.0
        alpha = int(160 * intensity)
        color = Color(0,0,0,alpha) if b < 0.5 else Color(255,255,255,alpha)
        draw_rectangle(0, 0, self.screen_w, self.screen_h, color)

    # ---------- Menú de pausa ----------
    def _pause_tab_button(self, x, y, w, h, label, selected, fsz):
        mx, my = get_mouse_x(), get_mouse_y()
        hovered = x <= mx <= x+w and y <= my <= y+h
        clicked = hovered and is_mouse_button_pressed(MOUSE_LEFT_BUTTON)
        bg = Color(70,70,75,230) if not (hovered or selected) else Color(95,95,102,240)
        self._draw_panel(x, y, w, h, bg, Color(0,0,0,210), 0.18)
        draw_text(label, x + 12, y + (h - fsz(18))//2, fsz(18), RAYWHITE)
        return clicked

    def _draw_pause_menu(self, ui_dims, fsz):
        w = int(self.screen_w*0.70)
        h = int(self.screen_h*0.70)
        x = (self.screen_w - w)//2
        y = (self.screen_h - h)//2
        self._draw_panel(x, y, w, h, Color(245,245,245,255), Color(60,60,60,230), 0.08)
        draw_text("PAUSA", x+16, y+14, fsz(28), BLACK)
        # Tabs
        tab_w = int(w*0.22)
        tab_h = 38
        tab_gap = 8
        tabs = [(PAUSE_TAB_MAIN, "General"), (PAUSE_TAB_VIDEO, "Video"), (PAUSE_TAB_AUDIO, "Audio"), (PAUSE_TAB_GAME, "Juego")]
        tx = x+16
        ty = y+56
        for t_id, t_name in tabs:
            clicked = self._pause_tab_button(tx, ty, tab_w, tab_h, t_name, self.ui_state["pause_tab"]==t_id, fsz)
            if clicked:
                self.ui_state["pause_tab"] = t_id
            ty += tab_h + tab_gap
        # Content panel
        cx = x+16+tab_w+16
        cy = y+56
        cw = w - (cx - x) - 16
        ch = h - (cy - y) - 16
        self._draw_panel(cx, cy, cw, ch, Color(255,255,255,255), Color(90,90,90,230), 0.06)
        if self.ui_state["pause_tab"] == PAUSE_TAB_MAIN:
            self._pause_content_main(cx, cy, cw, ch, fsz)
        elif self.ui_state["pause_tab"] == PAUSE_TAB_VIDEO:
            self._pause_content_video(cx, cy, cw, ch, fsz)
        elif self.ui_state["pause_tab"] == PAUSE_TAB_AUDIO:
            self._pause_content_audio(cx, cy, cw, ch, fsz)
        else:
            self._pause_content_game(cx, cy, cw, ch, fsz)

    def _pause_content_main(self, x, y, w, h, fsz):
        by = y + 16
        bw = int(w*0.5)
        bh = 42
        if ui_helpers.draw_button_left(x+16, by, bw, bh, "Reanudar", font_size=fsz(20)):
            self.ingame_menu_open = False
        by += bh + 10
        near = self._player_near_cabin()
        label = "Guardar (en cabaña)" if near else "Guardar (acércate a una cabaña)"
        if ui_helpers.draw_button_left(x+16, by, bw, bh, label, font_size=fsz(18)) and near:
            self._sleep_and_save()
        by += bh + 10
        if ui_helpers.draw_button_left(x+16, by, bw, bh, "Menú principal", font_size=fsz(20)):
            self.confirm_menu = True
        by += bh + 10
        if ui_helpers.draw_button_left(x+16, by, bw, bh, "Salir del juego", font_size=fsz(20)):
            self.confirm_quit = True

        if self.confirm_menu or self.confirm_quit:
            mw, mh = int(w*0.7), 120
            mx, my = x + (w-mw)//2, y + (h-mh)//2
            self._draw_panel(mx, my, mw, mh, Color(250,250,250,255), Color(90,90,90,220), 0.06)
            msg = "¿Volver al menú principal?" if self.confirm_menu else "¿Salir del juego?"
            draw_text(msg, mx+16, my+12, fsz(22), BLACK)
            if ui_helpers.draw_button_left(mx+16, my+56, 120, 38, "Cancelar", font_size=fsz(18)):
                self.confirm_menu = False
                self.confirm_quit = False
            if ui_helpers.draw_button_left(mx+mw-120-16, my+56, 120, 38, "Aceptar", font_size=fsz(18)):
                if self.confirm_menu:
                    self.state = STATE_MAIN_MENU
                    self.ingame_menu_open = False
                    self.confirm_menu = False
                else:
                    self.running = False

    def _pause_content_video(self, x, y, w, h, fsz):
        draw_text("Brillo", x+16, y+16, fsz(18), BLACK)
        self.ui_state["brightness"] = ui_helpers.slider_horizontal(x+16, y+40, int(w*0.6), 18, self.ui_state["brightness"], "brightness_dragging", self.ui_state)
        draw_text("Mostrar rejilla", x+16, y+78, fsz(18), BLACK)
        if ui_helpers.draw_button_left(x+16, y+100, 160, 34, "Alternar", font_size=fsz(18)):
            self.ui_state["show_grid"] = not self.ui_state["show_grid"]
            self._apply_grid_visibility_to_scenes()

    def _pause_content_audio(self, x, y, w, h, fsz):
        draw_text("Volumen general", x+16, y+16, fsz(18), BLACK)
        self.ui_state["master_volume"] = ui_helpers.slider_horizontal(x+16, y+40, int(w*0.6), 18, self.ui_state["master_volume"], "master_dragging", self.ui_state)
        draw_text("Música", x+16, y+78, fsz(18), BLACK)
        self.ui_state["music_volume"] = ui_helpers.slider_horizontal(x+16, y+100, int(w*0.6), 18, self.ui_state["music_volume"], "music_dragging", self.ui_state)
        draw_text("Efectos", x+16, y+138, fsz(18), BLACK)
        self.ui_state["sfx_volume"] = ui_helpers.slider_horizontal(x+16, y+160, int(w*0.6), 18, self.ui_state["sfx_volume"], "sfx_dragging", self.ui_state)

    def _pause_content_game(self, x, y, w, h, fsz):
        draw_text("Opciones de juego", x+16, y+16, fsz(18), BLACK)
        draw_text("Cabañas = punto de guardado (E).", x+16, y+44, fsz(16), Color(40,40,40,255))

    # ---------- Loading overlay ----------
    def _draw_loading_overlay(self, fsz) -> None:
        if not self.loading:
            return
        if self.trans_elapsed < FADE_TIME:
            alpha = int((self.trans_elapsed / FADE_TIME) * 255)
        elif self.trans_elapsed < FADE_TIME + HOLD_TIME:
            alpha = 255
        elif self.trans_elapsed < TRANSITION_TIME:
            alpha = int((1.0 - (self.trans_elapsed - FADE_TIME - HOLD_TIME) / FADE_TIME) * 255)
        else:
            alpha = 0
        draw_rectangle(0, 0, self.screen_w, self.screen_h, Color(30, 30, 30, max(0, min(255, alpha))))
        if self.loading_texture is None:
            fs = fsz(28)
            draw_text("Cargando...", self.screen_w // 2 - measure_text("Cargando...", fs) // 2, self.screen_h // 2 - fs // 2, fs, Color(220, 220, 220, max(120, alpha)))
        else:
            tex_w = self.loading_texture.width
            tex_h = self.loading_texture.height
            scale = min(self.screen_w / tex_w, self.screen_h / tex_h)
            draw_w = int(tex_w * scale)
            draw_h = int(tex_h * scale)
            draw_x = (self.screen_w - draw_w) // 2
            draw_y = (self.screen_h - draw_h) // 2
            draw_texture_ex(self.loading_texture, Vector2(draw_x, draw_y), 0.0, scale, Color(255,255,255,alpha))

    # ---------- Cabañas ----------
    def _setup_cabins(self) -> None:
        self.cabins = {0: [], 1: [], 2: [], 3: [], 4: []}
        for idx in (2, 3, 4):
            sc = self.scenes[idx-1]
            w, h = sc.size.x, sc.size.y
            if idx == 2:
                cx, cy = w*0.32, h*0.40
            elif idx == 3:
                cx, cy = w*0.62, h*0.36
            else:
                cx, cy = w*0.46, h*0.68
            rw, rh = 120, 90
            self.cabins[idx] = [Rectangle(cx - rw/2, cy - rh/2, rw, rh)]

    def _draw_cabins_world(self) -> None:
        idx = self.active_scene_index + 1
        for r in self.cabins.get(idx, []):
            draw_rectangle(int(r.x), int(r.y), int(r.width), int(r.height), Color(145, 112, 80, 255))
            draw_rectangle_lines(int(r.x), int(r.y), int(r.width), int(r.height), Color(30, 20, 10, 255))
            pw, ph = int(r.width*0.22), int(r.height*0.45)
            px = int(r.x + r.width*0.39)
            py = int(r.y + r.height - ph - 6)
            draw_rectangle(px, py, pw, ph, Color(80, 58, 40, 255))
            draw_rectangle_lines(px, py, pw, ph, BLACK)
            tx1 = Vector2(r.x-6, r.y+10)
            tx2 = Vector2(r.x+r.width+6, r.y+10)
            tx3 = Vector2(r.x+r.width/2, r.y-24)
            draw_triangle(tx1, tx2, tx3, Color(110, 75, 50, 255))
            draw_triangle_lines(tx1, tx2, tx3, BLACK)

    def _player_rect(self) -> Rectangle:
        s = float(self.player.size)
        half = s*0.5
        return Rectangle(self.player.position.x - half, self.player.position.y - half, s, s)

    def _player_near_cabin(self) -> bool:
        idx = self.active_scene_index + 1
        pr = self._player_rect()
        for r in self.cabins.get(idx, []):
            cx, cy = (r.x + r.width/2), (r.y + r.height/2)
            dx = pr.x + pr.width/2 - cx
            dy = pr.y + pr.height/2 - cy
            if (dx*dx + dy*dy) ** 0.5 <= max(r.width, r.height)*0.68:
                return True
        return False

    def _collides_cabin(self, test_x: float, test_y: float) -> bool:
        idx = self.active_scene_index + 1
        s = float(self.player.size)
        rect = Rectangle(test_x - s/2, test_y - s/2, s, s)
        for r in self.cabins.get(idx, []):
            if check_collision_recs(rect, r):
                return True
        return False

    def _draw_sleep_prompt(self, fsz) -> None:
        if self._player_near_cabin():
            txt = "Dormir / Guardar [E]"
            fs = fsz(20)
            x = int(self.screen_w*0.5 - measure_text(txt, fs)/2)
            y = int(self.screen_h*0.72)
            self._draw_panel(x-10, y-6, measure_text(txt, fs)+20, fs+14, Color(20,20,20,150), Color(0,0,0,200), 0.35)
            self._draw_text_shadow(txt, x, y, fs, Color(240,240,240,255))

    def _sleep_and_save(self) -> None:
        """Descansar y guardar: avanza 8 horas y persiste inventario/posición/tiempo."""
        # +8 horas
        spd = self.clock.seconds_per_day
        self.clock.elapsed += (8.0 / 24.0) * spd

        # recuperación
        self.player.hp = getattr(self.player, "max_hp", 100)
        self.player.stamina = self.player.max_stamina

        # guardar
        data = self._build_save_data()
        if not self.current_save_id:
            self.current_save_id = self.save_mgr.create(data, name=(self.current_save_name or "Partida"))
            self.current_save_name = self.save_mgr.load(self.current_save_id).get("name", "Partida")
        else:
            self.current_save_id = self.save_mgr.save(self.current_save_id, data)

    # ---------- Guardar/cargar ----------
    def _serialize_inventory(self) -> List[dict]:
        """Convierte TODO el inventario a una lista [{id, qty}], soportando get_slot(row,col)."""
        items: List[dict] = []
        try:
            rows = int(getattr(self.inventory, "rows", 0)) or 0
            cols = int(getattr(self.inventory, "cols", 0)) or 0
            if rows > 0 and cols > 0 and hasattr(self.inventory, "get_slot") and callable(self.inventory.get_slot):
                for r in range(rows):
                    for c in range(cols):
                        try:
                            slot = self.inventory.get_slot(r, c)
                            info = self._slot_item_info(slot)
                            if info:
                                items.append({"id": info[0], "qty": int(info[1])})
                        except Exception:
                            pass
            else:
                # Fallback: recorrer lista lineal de slots
                for slot in getattr(self.inventory, "slots", []):
                    info = self._slot_item_info(slot)
                    if info:
                        items.append({"id": info[0], "qty": int(info[1])})
        except Exception:
            pass
        return items

    def _load_inventory_from_dump(self, dump: List[dict]) -> None:
        # Limpia y repuebla usando el API público
        try:
            if hasattr(self.inventory, "clear_all"):
                self.inventory.clear_all()
            else:
                for s in getattr(self.inventory, "slots", []):
                    try:
                        s.clear()
                    except Exception:
                        pass
        except Exception:
            pass
        for it in dump or []:
            try:
                self.inventory.add_item(it["id"], int(it.get("qty", 1)))
            except Exception:
                pass

    def _build_save_data(self) -> dict:
        return {
            "id": self.current_save_id or "",
            "name": self.current_save_name or "Partida",
            "scene_index": self.active_scene_index + 1,
            "player": {"x": float(self.player.position.x), "y": float(self.player.position.y)},
            "clock_elapsed": float(self.clock.elapsed),
            "seconds_per_day": float(self.clock.seconds_per_day),
            "inventory": self._serialize_inventory(),
        }

    def _apply_save_data(self, data: dict) -> None:
        idx = max(1, int(data.get("scene_index", 1)))
        self.active_scene_index = min(len(self.scenes)-1, idx-1)
        p = data.get("player", {"x": self._scene_center(self.scenes[self.active_scene_index]).x,
                                 "y": self._scene_center(self.scenes[self.active_scene_index]).y})
        self.player.position = Vector2(float(p.get("x", 0.0)), float(p.get("y", 0.0)))
        self.player.destination = Vector2(self.player.position.x, self.player.position.y)
        self.clock.elapsed = float(data.get("clock_elapsed", 0.0))
        self.clock.seconds_per_day = float(data.get("seconds_per_day", self.clock.seconds_per_day))
        self._load_inventory_from_dump(data.get("inventory", []))
        self.camera.target = Vector2(self.player.position.x, self.player.position.y)
        self._clamp_camera_to_scene()

    # ---------- Nueva partida ----------
    def _reset_for_new_game(self) -> None:
        self.active_scene_index = 0  # Escenario 1
        start_pos = self._scene_center(self.scenes[self.active_scene_index])
        self.player.position = start_pos
        self.player.destination = Vector2(start_pos.x, start_pos.y)
        self._give_default_items()
        self.clock.elapsed = 6/24.0 * self.clock.seconds_per_day  # 06:00
        self.camera.target = Vector2(start_pos.x, start_pos.y)

    def _create_new_game(self, name: str) -> None:
        self._reset_for_new_game()
        data = self._build_save_data()
        new_id = self.save_mgr.create(data, name=name or "Partida")
        self.current_save_id = new_id
        self.current_save_name = self.save_mgr.load(new_id).get("name", name or "Partida")
        self._start_loading(self.active_scene_index, STATE_PLAY, keep_player_pos=True)

    # ---------- Selector de partidas ----------
    def _fmt_time_from_elapsed(self, elapsed: float, spd: float) -> str:
        frac = (elapsed % spd) / spd
        total_minutes = int(frac * 24 * 60)
        hh = total_minutes // 60
        mm = total_minutes % 60
        return f"{hh:02d}:{mm:02d}"

    def _day_from_elapsed(self, elapsed: float, spd: float) -> int:
        return int(elapsed // spd) + 1

    def _handle_rename_input(self):
        if not self._rename_slot_id:
            return
        key = get_key_pressed()
        while key > 0:
            if key == KEY_BACKSPACE:
                self._rename_buffer = self._rename_buffer[:-1]
            elif key in (KEY_ENTER, KEY_KP_ENTER):
                self.save_mgr.rename(self._rename_slot_id, self._rename_buffer)
                self._rename_slot_id = None
                break
            else:
                ch = get_char_pressed()
                while ch > 0:
                    if 32 <= ch <= 126 or ch >= 161:
                        self._rename_buffer += chr(ch)
                    ch = get_char_pressed()
            key = get_key_pressed()

    def _handle_newgame_name_input(self):
        key = get_key_pressed()
        while key > 0:
            if key == KEY_BACKSPACE:
                self._newgame_name = self._newgame_name[:-1]
            elif key in (KEY_ENTER, KEY_KP_ENTER):
                if self._newgame_name.strip():
                    self._create_new_game(self._newgame_name.strip())
                    self._newgame_modal_open = False
                break
            else:
                ch = get_char_pressed()
                while ch > 0:
                    if 32 <= ch <= 126 or ch >= 161:
                        self._newgame_name += chr(ch)
                    ch = get_char_pressed()
            key = get_key_pressed()

    def _draw_save_slots(self, fsz) -> None:
        # Fondo cuadriculado sutil
        draw_rectangle(0, 0, self.screen_w, self.screen_h, Color(245,245,245,255))
        grid_c = Color(0, 0, 0, 10)
        cell = max(48, int(self.screen_h * 0.08))
        for x in range(0, self.screen_w, cell):
            draw_line(x, 0, x, self.screen_h, grid_c)
        for y in range(0, self.screen_h, cell):
            draw_line(0, y, self.screen_w, y, grid_c)

        # Título
        title = "PARTIDAS"
        fs_title = fsz(36)
        draw_text(title, 20, int(self.screen_h*0.08), fs_title, Color(25, 25, 25, 255))

        slots = self.save_mgr.list_slots()
        panel_x = int(self.screen_w*0.10)
        panel_w = int(self.screen_w*0.80)
        row_h = max(86, int(self.screen_h*0.11))
        gap = 12
        y = int(self.screen_h*0.18)

        def season_strip(season: str) -> Color:
            return {"Primavera": Color(120, 180, 120, 255),
                    "Verano":    Color(110, 160, 220, 255),
                    "Otoño":     Color(200, 140,  70, 255),
                    "Invierno":  Color(160, 180, 210, 255)}.get(season, Color(150,150,150,255))

        fs_row = fsz(22)
        for i, s in enumerate(slots):
            row_y = y + i*(row_h + gap)
            # tarjeta
            self._draw_panel(panel_x, row_y, panel_w, row_h, Color(252,252,252,255), Color(120,120,120,220), 0.06)
            # banda estación
            elapsed = float(s["clock_elapsed"])
            spd = float(s["seconds_per_day"])
            day = self._day_from_elapsed(elapsed, spd)
            season_names = GameClock.SEASONS
            season = season_names[((day-1)//30) % len(season_names)]
            draw_rectangle(panel_x, row_y, 8, row_h, season_strip(season))

            name = s["name"]
            hhmm = self._fmt_time_from_elapsed(elapsed, spd)
            info = f"{name}   |   Escena {s['scene_index']}   |   Día {day}  {hhmm}"
            draw_text(info, panel_x+18, row_y+12, fs_row, BLACK)
            draw_text(f"Modificado: {s['updated']}", panel_x+18, row_y+12+fs_row+6, fsz(16), Color(60,60,60,255))

            # botones
            btn_w = 140
            btn_h = 38
            bx = panel_x + panel_w - btn_w - 16
            by = row_y + (row_h - btn_h)//2

            # CARGAR
            if ui_helpers.draw_button_left(bx, by, btn_w, btn_h, "Cargar", font_size=fsz(20)):
                data = self.save_mgr.load(s["id"])
                if data:
                    self.current_save_id = s["id"]
                    self.current_save_name = data.get("name", s["id"])
                    self._apply_save_data(data)
                    self._start_loading(self.active_scene_index, STATE_PLAY, keep_player_pos=True)
                    return

            # ELIMINAR
            if ui_helpers.draw_button_left(bx - (btn_w+10), by, btn_w, btn_h, "Eliminar", font_size=fsz(20)):
                self.save_mgr.delete(s["id"])
                return  # refrescar la lista

            # RENOMBRAR
            if ui_helpers.draw_button_left(bx - 2*(btn_w+10), by, btn_w, btn_h, "Renombrar", font_size=fsz(20)):
                self._rename_slot_id = s["id"]
                self._rename_buffer = s["name"]

        # Renombrar (input línea inferior)
        if self._rename_slot_id:
            self._handle_rename_input()
            txt = f"Nuevo nombre: {self._rename_buffer}_"
            w = int(self.screen_w*0.60)
            x = (self.screen_w - w)//2
            ry = y + len(slots)*(row_h+gap) + 10
            self._draw_panel(x, ry, w, 60, Color(255,255,230,255), Color(100,100,80,230), 0.06)
            draw_text("Escribe y pulsa Enter para confirmar, Backspace para borrar", x+10, ry+8, fsz(16), BLACK)
            draw_text(txt, x+10, ry+32, fsz(20), BLACK)

        # Crear partida
        bottom_y = y + len(slots)*(row_h + gap) + (70 if self._rename_slot_id else 0) + 18
        if ui_helpers.draw_button_left(panel_x, bottom_y, 260, 46, "Crear partida", font_size=fsz(22)):
            self._newgame_modal_open = True
            self._newgame_name = ""

        # Modal nueva partida
        if self._newgame_modal_open:
            mw, mh = int(self.screen_w*0.46), 160
            mx, my = (self.screen_w-mw)//2, (self.screen_h-mh)//2
            self._draw_panel(mx, my, mw, mh, Color(250,250,250,255), Color(80,80,80,220), 0.06)
            draw_text("Nombre de la partida:", mx+18, my+16, fsz(24), BLACK)

            # caja de texto
            self._handle_newgame_name_input()
            box_h = 40
            box_w = mw - 36
            self._draw_panel(mx+18, my+56, box_w, box_h, Color(240,240,240,255), Color(90,90,90,230), 0.06)
            draw_text(self._newgame_name + "_", mx+24, my+64, fsz(20), BLACK)

            # botones
            if ui_helpers.draw_button_left(mx+mw-140-18, my+mh-44, 140, 38, "Crear", font_size=fsz(20)):
                if self._newgame_name.strip():
                    self._create_new_game(self._newgame_name.strip())
                    self._newgame_modal_open = False
            if ui_helpers.draw_button_left(mx+18, my+mh-44, 140, 38, "Cancelar", font_size=fsz(20)):
                self._newgame_modal_open = False


# export
__all__ = ["Game", "RESOLUTIONS"]
