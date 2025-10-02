# game.py

from __future__ import annotations
from typing import Optional

from pyray import *
from player import Player
from scene import Scene
import input_handler
import ui_helpers
from inventory import Inventory
from map_system import MapSystem

# Polígonos de zonas (nuevos)
from zones_geometry import (
    zone2_alaska_polygon,
    zone3_ppr_polygon,
    zone4_michigan_polygon,
)

# ------------------ Constantes ------------------

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

STATE_MAIN_MENU = "MAIN_MENU"
STATE_CONFIG    = "CONFIG"
STATE_PLAY      = "PLAY"
STATE_LOADING   = "LOADING"

# ------------------ Reloj del juego ------------------

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

# ------------------ Juego ------------------

class Game:
    def __init__(self, initial_res_index: int) -> None:

        # Ventana
        self.res_index = initial_res_index
        self.screen_w, self.screen_h = RESOLUTIONS[self.res_index]
        # Mundo grande (5x pantalla) para libertad de cámara
        self.scene_w, self.scene_h = self.screen_w * 5, self.screen_h * 5

        init_window(self.screen_w, self.screen_h, "ASTRA - NASA Space Apps")
        set_target_fps(60)

        # Estados
        self.state = STATE_MAIN_MENU
        self.running = True
        self.ingame_menu_open = False

        # Transición de carga
        self.loading = False
        self.trans_elapsed = 0.0
        self.target_scene: Optional[int] = None
        self.swapped = False
        self.post_load_state = STATE_PLAY

        # Mundo/escenas
        self.scenes = self._create_scenes()
        self.active_scene_index = 0
        self.player = Player(self._scene_center(self.scenes[self.active_scene_index]))

        # Sistemas
        self.inventory = Inventory(rows=4, cols=10)
        self.map_system = MapSystem(total_scenes=len(self.scenes))

        # Items de ejemplo
        self.inventory.add_item("seed_corn", 10)
        self.inventory.add_item("seed_wheat", 5)
        self.inventory.add_item("water", 20)
        self.inventory.add_item("fertilizer", 8)

        # Hotbar
        self.hotbar_size = min(9, self.inventory.cols)
        self.hotbar_index = 0

        # Cámara
        self.camera = Camera2D()
        self._update_camera_offset()
        self.camera.target = Vector2(self.player.position.x, self.player.position.y)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        # UI state
        self.ui_state = {
            "music_volume": 0.8,
            "sfx_volume": 0.9,
            "music_dragging": False,
            "sfx_dragging": False,
            "res_dropdown_open": False,
        }

        # Reloj
        self.clock = GameClock(seconds_per_day=300.0)

        # Textura de carga opcional
        self.loading_texture: Optional[Texture2D] = None
        self._load_assets()

    # ------------------ Helpers ------------------

    def _update_camera_offset(self) -> None:
        self.camera.offset = Vector2(self.screen_w / 2, self.screen_h / 2)

    def _scene_center(self, scene: Scene) -> Vector2:
        return Vector2(scene.size.x * 0.5, scene.size.y * 0.5)

    def _make_scene(self, scene_id: int, color: Color) -> Scene:
        size = Vector2(self.scene_w, self.scene_h)
        spawn = Vector2(self.scene_w * 0.5, self.scene_h * 0.5)
        return Scene(scene_id, size, color, spawn)

    def _create_scenes(self) -> list[Scene]:
        """Crea las escenas. 2–4 usan polígonos de zona (sin rectángulo gigante)."""
        s1 = self._make_scene(1, Color(70, 120, 200, 255))  # Escena 1 queda rectangular (área local)

        # Escena 2 — Alaska
        s2 = Scene(
            2,
            Vector2(self.scene_w, self.scene_h),
            Color(200, 120, 70, 255),
            Vector2(self.scene_w * 0.5, self.scene_h * 0.5),
            grid_cell_size=64,
            grid_enabled=True,
            polygon_norm=zone2_alaska_polygon(),
        )

        # Escena 3 — Dakota del Norte (PPR)
        s3 = Scene(
            3,
            Vector2(self.scene_w, self.scene_h),
            Color(80, 160, 110, 255),
            Vector2(self.scene_w * 0.5, self.scene_h * 0.5),
            grid_cell_size=64,
            grid_enabled=True,
            polygon_norm=zone3_ppr_polygon(),
        )

        # Escena 4 — Michigan (Leelanau)
        s4 = Scene(
            4,
            Vector2(self.scene_w, self.scene_h),
            Color(160, 80, 160, 255),
            Vector2(self.scene_w * 0.5, self.scene_h * 0.5),
            grid_cell_size=64,
            grid_enabled=True,
            polygon_norm=zone4_michigan_polygon(),
        )

        return [s1, s2, s3, s4]

    def _load_assets(self) -> None:
        if LOADING_IMAGE_PATH is not None:
            try:
                self.loading_texture = load_texture(LOADING_IMAGE_PATH)
            except Exception:
                print(f"Error cargando textura: {LOADING_IMAGE_PATH}")
                self.loading_texture = None

    def _unload_assets(self) -> None:
        if self.loading_texture is not None:
            unload_texture(self.loading_texture)
            self.loading_texture = None

    # ------------------ Bucle principal ------------------

    def run(self) -> None:
        while self.running and not window_should_close():
            dt = get_frame_time()
            self._handle_input()
            self._update(dt)
            self._draw()

        self._unload_assets()
        close_window()

    # ------------------ Entrada ------------------

    def _handle_input(self) -> None:
        # Inventario (I)
        if self.state == STATE_PLAY and not self.loading:
            if is_key_pressed(KEY_I):
                if self.map_system.is_open:
                    self.map_system.is_open = False
                self.inventory.toggle()

        # Mapa (M)
        if self.state == STATE_PLAY and not self.loading:
            if is_key_pressed(KEY_M):
                if self.inventory.is_open:
                    self.inventory.is_open = False
                self.map_system.toggle()

        # ESC
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

        # Menú in-game (P)
        if self.state == STATE_PLAY and is_key_pressed(KEY_P):
            if self.inventory.is_open or self.map_system.is_open:
                self.inventory.is_open = False
                self.map_system.is_open  = False
            else:
                self.ingame_menu_open = not self.ingame_menu_open

        # Selección de escena por CLICK en el MAPA
        if (
            self.state == STATE_PLAY
            and not self.loading
            and self.map_system.is_open
            and not self.ingame_menu_open
        ):
            if is_mouse_button_pressed(MOUSE_LEFT_BUTTON):
                next_idx = -1
                if hasattr(self.map_system, "handle_click"):
                    try:
                        next_idx = self.map_system.handle_click(self.screen_w, self.screen_h)
                    except Exception:
                        next_idx = -1

                if (
                    isinstance(next_idx, int)
                    and 0 <= next_idx < len(self.scenes)
                    and next_idx != self.active_scene_index
                ):
                    self._start_loading(next_idx, STATE_PLAY)
                    self.map_system.is_open = False
                    self.inventory.is_open  = False
                    self.ingame_menu_open   = False

        # Hotbar: rueda y 1..9
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

        # Importante: NO hay teclas 1–4 para cambiar escena (solo mapa)

    # ------------------ Update ------------------

    def _update(self, dt: float) -> None:
        # Transición de carga
        if self.loading:
            self.trans_elapsed += dt
            if (not self.swapped) and (self.trans_elapsed >= FADE_TIME):
                if self.target_scene is not None:
                    self.active_scene_index = self.target_scene
                    # Reposicionar al centro de la nueva escena
                    self.player.position = self._scene_center(self.scenes[self.active_scene_index])
                    self.player.destination = self.player.position
                    self.camera.target = Vector2(self.player.position.x, self.player.position.y)
                self.swapped = True

            if self.trans_elapsed >= TRANSITION_TIME:
                self._end_loading()
                self.state = self.post_load_state

        # Actualización normal
        if (
            self.state == STATE_PLAY
            and not self.loading
            and not self.ingame_menu_open
            and not self.inventory.is_open
            and not self.map_system.is_open
        ):
            mouse_world = get_screen_to_world_2d(get_mouse_position(), self.camera)
            p_input = input_handler.get_player_input(self.player.position, self.player.destination, mouse_world)

            # Guardar pos anterior
            old_x, old_y = self.player.position.x, self.player.position.y

            # Mover jugador
            self.player.update(p_input, dt)

            # --- COLISIÓN con límites de la zona (collisions.py) ---
            scene = self.scenes[self.active_scene_index]
            cm = getattr(scene, "collision_map", None)

            if cm is not None:
                size = float(self.player.size)
                half = size * 0.5
                cs = scene.grid_cell_size

                def collides_at(px: float, py: float) -> bool:
                    return cm.rect_collides(px - half, py - half, size, size, cs, cs)

                # Separación por ejes: intenta mover en X, luego en Y
                new_x, new_y = self.player.position.x, self.player.position.y

                # mover en X
                test_x = new_x
                if collides_at(test_x, old_y):
                    test_x = old_x

                # mover en Y (con X ya aplicado)
                test_y = new_y
                if collides_at(test_x, test_y):
                    if collides_at(test_x, old_y):
                        test_y = old_y  # choca también en Y, vuelve
                    else:
                        # prueba solo Y
                        if collides_at(old_x, new_y):
                            test_y = old_y

                self.player.position.x = test_x
                self.player.position.y = test_y
                # Asegura que el destino no quede fuera
                if collides_at(self.player.destination.x, self.player.destination.y):
                    self.player.destination = Vector2(self.player.position.x, self.player.position.y)

            # Zoom
            if is_key_down(KEY_EQUAL) or is_key_down(KEY_KP_ADD):
                self.camera.zoom += 1.0 * dt
            if is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT):
                self.camera.zoom -= 1.0 * dt
            self.camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.camera.zoom))

            # Seguir al jugador
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)

        # Reloj del juego
        self.clock.update(dt)

    # ------------------ Transiciones ------------------

    def _start_loading(self, target_scene_index: int, next_state: str) -> None:
        self.loading = True
        self.trans_elapsed = 0.0
        self.target_scene = target_scene_index
        self.swapped = False
        self.post_load_state = next_state
        self.state = STATE_LOADING

    def _end_loading(self) -> None:
        self.loading = False
        self.target_scene = None
        self.swapped = False
        self.trans_elapsed = 0.0

    # ------------------ Dibujo ------------------

    def _draw(self) -> None:
        begin_drawing()
        clear_background(RAYWHITE)

        ui = ui_helpers.calculate_ui_dimensions(self.screen_w, self.screen_h)
        fsz = lambda base: ui_helpers.calc_font(self.screen_h, base)

        if self.state == STATE_MAIN_MENU:
            self._draw_main_menu(ui, fsz)
        elif self.state == STATE_CONFIG:
            self._draw_config(ui, fsz)
        elif self.state in (STATE_PLAY, STATE_LOADING):
            self._draw_play_state(ui, fsz)
            self._draw_loading_overlay(fsz)
        else:
            draw_text("Estado desconocido", 10, 10, fsz(22), RED)

        end_drawing()

    def _draw_main_menu(self, ui_dims: dict, fsz) -> None:
        title = "ASTRA"
        tw = ui_helpers.measure(title, fsz(48))
        draw_text(title, (self.screen_w - tw) // 2, int(self.screen_h * 0.15), fsz(48), DARKBLUE)

        x = ui_dims["left_margin"]
        bw = ui_dims["main_button_w"]
        bh = ui_dims["main_button_h"]
        gap = int(self.screen_h * 0.03)
        y0 = int(self.screen_h * 0.35)

        if ui_helpers.draw_button_left(x, y0 + 0 * (bh + gap), bw, bh, "Jugar", font_size=fsz(24)):
            self._start_loading(self.active_scene_index, STATE_PLAY)

        if ui_helpers.draw_button_left(x, y0 + 1 * (bh + gap), bw, bh, "Configuración", font_size=fsz(24)):
            self.state = STATE_CONFIG
            self.ui_state["res_dropdown_open"] = False

        if ui_helpers.draw_button_left(x, y0 + 2 * (bh + gap), bw, bh, "Salir", font_size=fsz(24)):
            self.running = False

    def _draw_config(self, ui_dims: dict, fsz) -> None:
        draw_text("CONFIGURACIÓN", ui_dims["left_margin"], int(self.screen_h * 0.12), fsz(32), BLACK)

        block_x = ui_dims["left_margin"]
        block_y = int(self.screen_h * 0.22)
        slider_w = ui_dims["slider_w"]
        slider_h = ui_dims["slider_h"]
        gap_y = int(self.screen_h * 0.06)

        # Volumen música
        draw_text("Música", block_x, block_y - fsz(18), fsz(18), BLACK)
        self.ui_state["music_volume"] = ui_helpers.slider_horizontal(
            block_x, block_y, slider_w, slider_h, self.ui_state["music_volume"], "music_dragging", self.ui_state
        )

        # Volumen SFX
        sfx_y = block_y + gap_y
        draw_text("SFX", block_x, sfx_y - fsz(18), fsz(18), BLACK)
        self.ui_state["sfx_volume"] = ui_helpers.slider_horizontal(
            block_x, sfx_y, slider_w, slider_h, self.ui_state["sfx_volume"], "sfx_dragging", self.ui_state
        )

        # Resoluciones
        drop_y = sfx_y + gap_y
        draw_text("Resolución", block_x, drop_y - fsz(18), fsz(18), BLACK)

        drop_w = int(slider_w * 0.9)
        drop_h = max(28, ui_dims["button_h"])
        drop_label = f"{RESOLUTIONS[self.res_index][0]}x{RESOLUTIONS[self.res_index][1]}"
        hovered, clicked = ui_helpers.button_left_rect(block_x, drop_y, drop_w, drop_h, drop_label, fsz(18))
        if clicked:
            self.ui_state["res_dropdown_open"] = not self.ui_state["res_dropdown_open"]

        if self.ui_state["res_dropdown_open"]:
            opt_h = drop_h
            max_visible = len(RESOLUTIONS)
            for i in range(max_visible):
                oy = drop_y + (i + 1) * (opt_h + 4)
                txt = f"{RESOLUTIONS[i][0]}x{RESOLUTIONS[i][1]}"
                _, opt_clicked = ui_helpers.button_left_rect(block_x, oy, drop_w, opt_h, txt, fsz(18))
                if opt_clicked:
                    self.res_index = i
                    self.ui_state["res_dropdown_open"] = False
                    break

        # Botones aplicar/volver
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
        """Aplica la resolución seleccionada (y escala el mundo 5x)."""
        new_w, new_h = RESOLUTIONS[self.res_index]
        if new_w != self.screen_w or new_h != self.screen_h:
            self.screen_w, self.screen_h = new_w, new_h
            self.scene_w, self.scene_h = new_w * 5, new_h * 5
            set_window_size(self.screen_w, self.screen_h)

            # Recrear escenas/mapa y reubicar jugador
            self.scenes = self._create_scenes()
            self.map_system = MapSystem(total_scenes=len(self.scenes))
            self.player.position = self._scene_center(self.scenes[self.active_scene_index])

            # Cámara
            self._update_camera_offset()
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)

    def _draw_play_state(self, ui_dims: dict, fsz) -> None:
        begin_mode_2d(self.camera)
        self.scenes[self.active_scene_index].draw()
        self.player.draw()
        end_mode_2d()

        # HUD compacto
        self._draw_hud(fsz)

        # Inventario y Mapa
        self.inventory.draw(self.screen_w, self.screen_h)
        self.map_system.draw(self.screen_w, self.screen_h, self.active_scene_index)

        # Menú in-game
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

    # ---------- HUD ----------
    def _current_location_name(self) -> str:
        try:
            return self.map_system.scene_names[self.active_scene_index]
        except Exception:
            return f"Escena {self.active_scene_index + 1}"

    def _draw_bar(self, x: int, y: int, w: int, h: int, value: float, max_value: float, color_fill: Color, label: str) -> None:
        ratio = 0.0 if max_value <= 0 else max(0.0, min(1.0, value / max_value))
        draw_rectangle(x, y, w, h, Color(40, 40, 40, 200))
        draw_rectangle(x + 2, y + 2, int((w - 4) * ratio), h - 4, color_fill)
        draw_rectangle_lines(x, y, w, h, BLACK)
        txt = f"{label}: {int(value)}/{int(max_value)}"
        fs = max(14, h - 2)
        draw_text(txt, x + 8, y - fs - 2, fs, BLACK)

    def _draw_hotbar_right(self) -> None:
        slot_size = min(64, int(self.screen_h * 0.07))
        pad = max(6, int(slot_size * 0.1))
        total_h = self.hotbar_size * (slot_size + pad) - pad
        x = self.screen_w - slot_size - 16
        y = (self.screen_h - total_h) // 2

        for i in range(self.hotbar_size):
            sx = x
            sy = y + i * (slot_size + pad)

            bg = Color(80, 70, 60, 220)
            if i == self.hotbar_index:
                bg = Color(120, 200, 255, 240)
                draw_rectangle(sx - 4, sy - 4, slot_size + 8, slot_size + 8, Color(255, 255, 255, 40))
            draw_rectangle(sx, sy, slot_size, slot_size, bg)
            draw_rectangle_lines(sx, sy, slot_size, slot_size, Color(40, 35, 30, 255))

            num_text = str(i + 1)
            nf = max(14, int(slot_size * 0.25))
            draw_text(num_text, sx + 6, sy + 4, nf, BLACK)

            inv_idx = i
            if inv_idx < len(self.inventory.slots):
                slot = self.inventory.slots[inv_idx]
                if not slot.is_empty():
                    icon_size = int(slot_size * 0.7)
                    ix = sx + (slot_size - icon_size) // 2
                    iy = sy + (slot_size - icon_size) // 2
                    draw_rectangle(ix, iy, icon_size, icon_size, slot.item.icon_color)
                    draw_rectangle_lines(ix, iy, icon_size, icon_size, BLACK)
                    if slot.quantity > 1:
                        qty_text = str(slot.quantity)
                        qf = max(14, int(slot_size * 0.28))
                        draw_text(qty_text, sx + slot_size - measure_text(qty_text, qf) - 6,
                                  sy + slot_size - qf - 4, qf, WHITE)

    def _draw_hud(self, fsz) -> None:
        # Panel superior: hora / día / temporada / lugar
        top_text = f"{self.clock.time_hhmm()}  |  Día {self.clock.day}  |  {self.clock.season_name()}  |  {self._current_location_name()}"
        font = fsz(22)
        tw = measure_text(top_text, font)
        draw_rectangle((self.screen_w - tw) // 2 - 12, 10, tw + 24, font + 16, Color(255, 255, 255, 140))
        draw_rectangle_lines((self.screen_w - tw) // 2 - 12, 10, tw + 24, font + 16, Color(40, 40, 40, 200))
        draw_text(top_text, (self.screen_w - tw) // 2, 18, font, BLACK)

        # Vida y Estamina
        bar_w = int(self.screen_w * 0.25)
        bar_h = max(16, int(self.screen_h * 0.02))
        base_x = 16
        base_y = 16 + font + 20

        # Vida (usa Player.hp si lo añadiste; si no, puedes mapear a stamina)
        if hasattr(self.player, "hp"):
            self._draw_bar(base_x, base_y, bar_w, bar_h, getattr(self.player, "hp", 100.0), getattr(self.player, "max_hp", 100.0), Color(220, 70, 70, 255), "HP")
        else:
            # fallback: muestra solo estamina como HP para no romper HUD
            self._draw_bar(base_x, base_y, bar_w, bar_h, self.player.stamina, self.player.max_stamina, Color(220, 70, 70, 255), "HP")

        # Estamina
        self._draw_bar(base_x, base_y + bar_h + 10, bar_w, bar_h, self.player.stamina, self.player.max_stamina, Color(70, 180, 90, 255), "STA")

        # Hotbar
        self._draw_hotbar_right()

    # ------------------ Overlay de carga ------------------

    def _draw_loading_overlay(self, fsz) -> None:
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
            fs = fsz(28)
            draw_text("Cargando...", self.screen_w // 2 - measure_text("Cargando...", fs)//2, self.screen_h // 2 - fs // 2, fs, Color(220, 220, 220, max(120, alpha)))
