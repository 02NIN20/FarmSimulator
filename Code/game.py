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

# Polígonos densos tipo mapa (definidos en zones_geometry.py)
from zones_geometry import (
    zone2_alaska_polygon,
    zone3_ppr_polygon,
    zone4_michigan_polygon,
)

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


class Game:
    def __init__(self, initial_res_index: int) -> None:
        self.res_index = initial_res_index
        self.screen_w, self.screen_h = RESOLUTIONS[self.res_index]
        self.scene_w, self.scene_h = self.screen_w * 5, self.screen_h * 5

        init_window(self.screen_w, self.screen_h, "ASTRA - NASA Space Apps")
        set_exit_key(0)
        set_target_fps(60)

        self.state = STATE_MAIN_MENU
        self.running = True
        self.ingame_menu_open = False

        self.loading = False
        self.trans_elapsed = 0.0
        self.target_scene: Optional[int] = None
        self.swapped = False
        self.post_load_state = STATE_PLAY

        self.scenes = self._create_scenes()
        self.active_scene_index = 0
        self.player = Player(self._scene_center(self.scenes[self.active_scene_index]))

        self.inventory = Inventory(rows=4, cols=10)
        self.map_system = MapSystem(total_scenes=len(self.scenes))

        # Ítems ejemplo
        self.inventory.add_item("seed_corn", 10)
        self.inventory.add_item("seed_wheat", 5)
        self.inventory.add_item("water", 20)
        self.inventory.add_item("fertilizer", 8)

        self.hotbar_size = min(9, self.inventory.cols)
        self.hotbar_index = 0

        self.camera = Camera2D()
        self._update_camera_offset()
        self.camera.target = Vector2(self.player.position.x, self.player.position.y)
        self.camera.rotation = 0.0
        self.camera.zoom = 1.0

        self.ui_state = {
            "music_volume": 0.8,
            "sfx_volume": 0.9,
            "music_dragging": False,
            "sfx_dragging": False,
            "res_dropdown_open": False,
        }

        self.clock = GameClock(seconds_per_day=300.0)

        self.loading_texture: Optional[Texture2D] = None
        self._load_assets()

    # ===================== Helpers =====================

    def _update_camera_offset(self) -> None:
        self.camera.offset = Vector2(self.screen_w / 2, self.screen_h / 2)

    def _scene_center(self, scene: Scene) -> Vector2:
        return Vector2(scene.size.x * 0.5, scene.size.y * 0.5)

    def _make_scene(self, scene_id: int, land: Color) -> Scene:
        size = Vector2(self.scene_w, self.scene_h)
        spawn = Vector2(self.scene_w * 0.5, self.scene_h * 0.5)
        return Scene(scene_id, size, land, spawn, land_color=land)

    def _clamp_camera_to_scene(self) -> None:
        """Evita que la cámara muestre fuera de la escena (adiós franjas blancas)."""
        scene = self.scenes[self.active_scene_index]
        half_w = (self.screen_w * 0.5) / max(0.001, self.camera.zoom)
        half_h = (self.screen_h * 0.5) / max(0.001, self.camera.zoom)
        tx = max(half_w, min(scene.size.x - half_w, self.camera.target.x))
        ty = max(half_h, min(scene.size.y - half_h, self.camera.target.y))
        self.camera.target = Vector2(tx, ty)

    # --- Ajuste de texto al ancho disponible ---
    def _fit_font(self, text: str, max_width: int, base: int, min_size: int = 14) -> int:
        size = base
        while size > min_size and measure_text(text, size) > max_width:
            size -= 1
        return max(min_size, size)

    # ===================== Crear escenas =====================

    def _create_scenes(self) -> list[Scene]:
        # Tono “pasto” por bioma
        LOCAL_LAND   = Color(128, 178, 112, 255)  # neutro
        ALASKA_LAND  = Color(100, 142, 120, 255)  # boreal
        PPR_LAND     = Color(160, 175,  90, 255)  # pradera
        MICH_LAND    = Color( 92, 150, 110, 255)  # bosque húmedo

        s1 = self._make_scene(1, LOCAL_LAND)

        s2 = Scene(
            2, Vector2(self.scene_w, self.scene_h), ALASKA_LAND,
            Vector2(self.scene_w * 0.5, self.scene_h * 0.5),
            grid_cell_size=48, grid_enabled=True,
            polygon_norm=zone2_alaska_polygon(), land_color=ALASKA_LAND
        )
        s3 = Scene(
            3, Vector2(self.scene_w, self.scene_h), PPR_LAND,
            Vector2(self.scene_w * 0.5, self.scene_h * 0.5),
            grid_cell_size=48, grid_enabled=True,
            polygon_norm=zone3_ppr_polygon(), land_color=PPR_LAND
        )
        s4 = Scene(
            4, Vector2(self.scene_w, self.scene_h), MICH_LAND,
            Vector2(self.scene_w * 0.5, self.scene_h * 0.5),
            grid_cell_size=48, grid_enabled=True,
            polygon_norm=zone4_michigan_polygon(), land_color=MICH_LAND
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

    # ===================== Bucle principal =====================

    def run(self) -> None:
        while self.running and not window_should_close():
            dt = get_frame_time()
            self._handle_input()
            self._update(dt)
            self._draw()
        self._unload_assets()
        close_window()

    # ===================== Entrada =====================

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

        # ESC: NO cierra el juego en ningún estado
        if is_key_pressed(KEY_ESCAPE):
            if self.state == STATE_MAIN_MENU:
                # No hace nada (antes salía del juego)
                pass
            elif self.state == STATE_CONFIG:
                # Vuelve al menú principal
                self.state = STATE_MAIN_MENU
                self.ui_state["res_dropdown_open"] = False
            elif self.state == STATE_PLAY:
                # Cierra paneles si están abiertos; si no, abre/cierra el menú in-game
                if self.inventory.is_open:
                    self.inventory.is_open = False
                elif self.map_system.is_open:
                    self.map_system.is_open = False
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

        # Hotbar: rueda y 1..9 (SOLO hotbar, NO cambia de escenas)
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

    # ===================== Update =====================

    def _update(self, dt: float) -> None:
        if self.loading:
            self.trans_elapsed += dt
            if (not self.swapped) and (self.trans_elapsed >= FADE_TIME):
                if self.target_scene is not None:
                    self.active_scene_index = self.target_scene
                    self.player.position = self._scene_center(self.scenes[self.active_scene_index])
                    self.player.destination = self.player.position
                    self.camera.target = Vector2(self.player.position.x, self.player.position.y)
                    self._clamp_camera_to_scene()
                self.swapped = True
            if self.trans_elapsed >= TRANSITION_TIME:
                self._end_loading()
                self.state = self.post_load_state

        if (
            self.state == STATE_PLAY
            and not self.loading
            and not self.ingame_menu_open
            and not self.inventory.is_open
            and not self.map_system.is_open
        ):
            mouse_world = get_screen_to_world_2d(get_mouse_position(), self.camera)
            p_input = input_handler.get_player_input(self.player.position, self.player.destination, mouse_world)

            old_x, old_y = self.player.position.x, self.player.position.y
            self.player.update(p_input, dt)

            # Colisión con contorno (CollisionMap de la escena activa)
            scene = self.scenes[self.active_scene_index]
            cm = getattr(scene, "collision_map", None)
            if cm is not None:
                size = float(self.player.size)
                half = size * 0.5
                cs = scene.grid_cell_size

                def collides_at(px: float, py: float) -> bool:
                    return cm.rect_collides(px - half, py - half, size, size, cs, cs)

                new_x, new_y = self.player.position.x, self.player.position.y

                # Eje X
                test_x = new_x
                if collides_at(test_x, old_y):
                    test_x = old_x

                # Eje Y
                test_y = new_y
                if collides_at(test_x, test_y):
                    if collides_at(test_x, old_y):
                        test_y = old_y
                    else:
                        if collides_at(old_x, new_y):
                            test_y = old_y

                self.player.position.x = test_x
                self.player.position.y = test_y

                # Ajusta destino si quedó fuera
                if collides_at(self.player.destination.x, self.player.destination.y):
                    self.player.destination = Vector2(self.player.position.x, self.player.position.y)

            # Zoom
            if is_key_down(KEY_EQUAL) or is_key_down(KEY_KP_ADD):
                self.camera.zoom += 1.0 * dt
            if is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT):
                self.camera.zoom -= 1.0 * dt
            self.camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, self.camera.zoom))

            # Seguir + CLAMP cámara
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)
            self._clamp_camera_to_scene()

        self.clock.update(dt)

    # ===================== Transiciones =====================

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

    # ===================== Dibujo =====================

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
        _, clicked = ui_helpers.button_left_rect(block_x, drop_y, drop_w, drop_h, drop_label, fsz(18))
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
        new_w, new_h = RESOLUTIONS[self.res_index]
        if new_w != self.screen_w or new_h != self.screen_h:
            self.screen_w, self.screen_h = new_w, new_h
            self.scene_w, self.scene_h = new_w * 5, new_h * 5
            set_window_size(self.screen_w, self.screen_h)

            self.scenes = self._create_scenes()
            self.map_system = MapSystem(total_scenes=len(self.scenes))
            self.player.position = self._scene_center(self.scenes[self.active_scene_index])

            self._update_camera_offset()
            self.camera.target = Vector2(self.player.position.x, self.player.position.y)
            self._clamp_camera_to_scene()

    def _draw_play_state(self, ui_dims: dict, fsz) -> None:
        begin_mode_2d(self.camera)
        self.scenes[self.active_scene_index].draw()
        self.player.draw()
        end_mode_2d()

        # HUD estilizado
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

    # ===================== Helpers visuales HUD =====================

    def _color_scale(self, c: Color, factor: float) -> Color:
        return Color(
            int(max(0, min(255, c.r * factor))),
            int(max(0, min(255, c.g * factor))),
            int(max(0, min(255, c.b * factor))),
            c.a
        )

    def _draw_text_shadow(self, text: str, x: int, y: int, fs: int, fg: Color) -> None:
        draw_text(text, x + 1, y + 1, fs, Color(0, 0, 0, 120))
        draw_text(text, x, y, fs, fg)

    def _draw_panel(self, x: int, y: int, w: int, h: int, fill: Color, border: Color, radius: float = 0.2) -> None:
        # sombra suave
        draw_rectangle(x + 2, y + 2, w, h, Color(0, 0, 0, 60))
        # rect redondeado (fallback a rect simple si no está la función)
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

        # Texto centrado dentro de la barra
        fs = max(14, h - 8)
        txt = f"{label} {int(value)}/{int(max_value)}"
        tx = x + (w - measure_text(txt, fs)) // 2
        ty = y + (h - fs) // 2
        self._draw_text_shadow(txt, tx, ty, fs, Color(245, 245, 245, 240))

    def _draw_hotbar_right(self) -> None:
        slot_size = min(60, int(self.screen_h * 0.068))
        pad = max(6, int(slot_size * 0.12))
        total_h = self.hotbar_size * (slot_size + pad) - pad
        x = self.screen_w - slot_size - 20
        y = (self.screen_h - total_h) // 2

        panel_w = slot_size + 20
        panel_h = total_h + 20
        self._draw_panel(x - 10, y - 10, panel_w, panel_h, Color(20, 20, 20, 130), Color(0, 0, 0, 180), radius=0.2)

        for i in range(self.hotbar_size):
            sx = x
            sy = y + i * (slot_size + pad)

            slot_bg = Color(60, 58, 55, 210)
            slot_border = Color(0, 0, 0, 200)
            self._draw_panel(sx, sy, slot_size, slot_size, slot_bg, slot_border, radius=0.2)

            if i == self.hotbar_index:
                draw_rectangle_lines(sx - 3, sy - 3, slot_size + 6, slot_size + 6, Color(255, 220, 120, 255))
                draw_rectangle_lines(sx - 1, sy - 1, slot_size + 2, slot_size + 2, Color(255, 255, 255, 90))

            num_text = str(i + 1)
            nf = max(12, int(slot_size * 0.23))
            self._draw_text_shadow(
                num_text,
                sx + slot_size - measure_text(num_text, nf) - 6,
                sy + 4,
                nf,
                Color(240, 240, 240, 230),
            )

            inv_idx = i
            if inv_idx < len(self.inventory.slots):
                slot = self.inventory.slots[inv_idx]
                if not slot.is_empty():
                    icon_size = int(slot_size * 0.72)
                    ix = sx + (slot_size - icon_size) // 2
                    iy = sy + (slot_size - icon_size) // 2
                    draw_rectangle(ix, iy, icon_size, icon_size, slot.item.icon_color)
                    draw_rectangle_lines(ix, iy, icon_size, icon_size, Color(0, 0, 0, 160))

                    if slot.quantity > 1:
                        qty_text = str(slot.quantity)
                        qf = max(12, int(slot_size * 0.26))
                        bx = sx + slot_size - measure_text(qty_text, qf) - 6
                        by = sy + slot_size - qf - 5
                        self._draw_text_shadow(qty_text, bx, by, qf, Color(255, 255, 255, 240))

    def _current_location_name(self) -> str:
        """Nombre legible de la escena actual (para el panel superior)."""
        try:
            return self.map_system.scene_names[self.active_scene_index]
        except Exception:
            return f"Escenario {self.active_scene_index + 1}"

    def _draw_hud(self, fsz) -> None:
        # Panel superior a todo lo ancho, texto autoajustado
        margin = 12
        panel_x = margin
        panel_y = margin
        panel_w = self.screen_w - margin * 2
        base_fs = fsz(22)
        top_text = f"{self.clock.time_hhmm()}  |  Día {self.clock.day}  |  {self.clock.season_name()}  |  {self._current_location_name()}"
        fs_fit = self._fit_font(top_text, panel_w - 28, base_fs, 14)
        panel_h = fs_fit + 18

        self._draw_panel(panel_x, panel_y, panel_w, panel_h, Color(240, 240, 240, 170), Color(30, 30, 30, 200), radius=0.18)
        text_x = panel_x + (panel_w - measure_text(top_text, fs_fit)) // 2
        self._draw_text_shadow(top_text, text_x, panel_y + 9, fs_fit, Color(20, 20, 20, 240))

        # Barras bajo el panel superior
        bar_gap_y = 10
        bar_w = min(int(self.screen_w * 0.32), 460)
        bar_h = max(20, int(self.screen_h * 0.026))
        bars_x = margin
        first_bar_y = panel_y + panel_h + bar_gap_y

        # HP
        hp_val = getattr(self.player, "hp", 100.0)
        hp_max = getattr(self.player, "max_hp", 100.0)
        self._draw_bar(bars_x, first_bar_y, bar_w, bar_h, hp_val, hp_max, Color(210, 70, 70, 255), "HP")

        # STA
        sta_y = first_bar_y + bar_h + 8
        self._draw_bar(bars_x, sta_y, bar_w, bar_h, self.player.stamina, self.player.max_stamina, Color(80, 180, 100, 255), "STA")

        # Hotbar derecha
        self._draw_hotbar_right()

    # ===================== Overlay de carga =====================

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
            draw_text(
                "Cargando...",
                self.screen_w // 2 - measure_text("Cargando...", fs) // 2,
                self.screen_h // 2 - fs // 2,
                fs,
                Color(220, 220, 220, max(120, alpha)),
            )
