"""minor changes (mentira xd)
"""

from __future__ import annotations

from pyray import *
from Classes import Player, Scene
import Input  # movimiento WASD/flechas

# Resoluciones disponibles
RESOLUTIONS = [
    (1920, 1080),
    (1600, 900),
    (1366, 768),
    (1280, 720),
    (1024, 576),
    (960, 540),
]

# Valores por defecto (inicial)
SCREEN_W, SCREEN_H = RESOLUTIONS[-1]  # empieza en 960x540 por defecto
SCENE_W, SCENE_H = SCREEN_W, SCREEN_H
MIN_ZOOM, MAX_ZOOM = 0.35, 3.0

# Wrappers por si la binding tiene otro nombre (seguridad)
_begin_mode_2d = begin_mode_2d if 'begin_mode_2d' in globals() else begin_mode2d
_end_mode_2d = end_mode_2d if 'end_mode_2d' in globals() else end_mode2d

# --- UI layout base ratios (relativos, lineales) ---
LEFT_MARGIN_RATIO = 0.04         # margen izquierdo relativo al ancho
BASE_BUTTON_WIDTH_RATIO = 0.26   # ancho base relativo al ancho de la ventana
BASE_BUTTON_HEIGHT_RATIO = 0.085 # alto base relativo al alto de la ventana
MAIN_BASE_BUTTON_WIDTH_RATIO = 0.18
MAIN_BASE_BUTTON_HEIGHT_RATIO = 0.07

SLIDER_WIDTH_RATIO = 0.28
SLIDER_HEIGHT_RATIO = 0.04

# referencia para cálculo de tamaño de fuente (escala lineal)
REF_H = 540.0

# --- helpers UI ---
def measure(text: str, size: int) -> int:
    return measure_text(text, size)

def calc_font(base_font: int) -> int:
    """Escalado lineal del tamaño de fuente según la altura de la ventana (base en REF_H)."""
    return max(12, int(base_font * (SCREEN_H / REF_H)))

def draw_button_left(x: int, y: int, w: int, h: int, text: str, font_size: int = 22):
    """Dibuja un botón rectángulo alineado a la izquierda (coordenadas dadas).
       Devuelve True si fue clickeado con el mouse en este frame."""
    mouse = get_mouse_position()
    mx, my = int(mouse.x), int(mouse.y)
    hovered = (mx >= x and mx <= x + w and my >= y and my <= y + h)
    bg = SKYBLUE if hovered else DARKGRAY
    txt_color = BLACK if hovered else WHITE

    draw_rectangle(x, y, w, h, bg)
    draw_rectangle_lines(x, y, w, h, BLACK)

    # texto alineado a la izquierda con padding interno
    draw_text(text, x + 8, y + (h - font_size) // 2, font_size, txt_color)

    clicked = hovered and is_mouse_button_pressed(MOUSE_LEFT_BUTTON)
    return clicked

def button_left_rect(x: int, y: int, w: int, h: int, text: str, font_size: int = 22):
    """Dibuja un botón y retorna (hovered, clicked)."""
    mouse = get_mouse_position()
    mx, my = int(mouse.x), int(mouse.y)
    hovered = (mx >= x and mx <= x + w and my >= y and my <= y + h)
    bg = SKYBLUE if hovered else DARKGRAY
    txt_color = BLACK if hovered else WHITE

    draw_rectangle(x, y, w, h, bg)
    draw_rectangle_lines(x, y, w, h, BLACK)
    draw_text(text, x + 8, y + (h - font_size) // 2, font_size, txt_color)

    clicked = hovered and is_mouse_button_pressed(MOUSE_LEFT_BUTTON)
    return hovered, clicked

# slider helper (returns value 0..1, handles drawing and dragging)
def slider_horizontal(x: int, y: int, w: int, h: int, value: float, dragging_flag_name: str, state_dict: dict) -> float:
    """Dibuja un slider horizontal (track + handle). value es 0..1.
       dragging_flag_name es la key en state_dict que guarda si el slider está en drag.
       Devuelve el nuevo valor (0..1)."""
    mouse = get_mouse_position()
    mx, my = mouse.x, mouse.y
    track_color = DARKGRAY
    handle_color = SKYBLUE

    # track (centro vertical del slider)
    track_h = max(4, int(h * 0.4))
    draw_rectangle(x, y + (h // 2) - (track_h // 2), w, track_h, track_color)

    # handle size: ahora 1% más grande que el alto del slider
    handle_h = max(6, int(h * 1.01))
    handle_w = max(6, int(h * 1.01))

    # handle position (centro según value)
    handle_x = int(x + max(0, min(w, value * w)) - handle_w // 2)
    handle_y = int(y + (h - handle_h) // 2)

    # detect drag start
    mouse_pressed = is_mouse_button_pressed(MOUSE_LEFT_BUTTON)
    mouse_down = is_mouse_button_down(MOUSE_LEFT_BUTTON)

    hovered_handle = (mx >= handle_x and mx <= handle_x + handle_w and my >= handle_y and my <= handle_y + handle_h)
    hovered_track = (mx >= x and mx <= x + w and my >= y and my <= y + h)
    if mouse_pressed and (hovered_handle or hovered_track):
        state_dict[dragging_flag_name] = True

    if not mouse_down:
        state_dict[dragging_flag_name] = False

    if state_dict.get(dragging_flag_name, False):
        rel = (mx - x) / max(1.0, w)
        value = max(0.0, min(1.0, rel))

    # draw handle
    draw_rectangle(handle_x, handle_y, handle_w, handle_h, handle_color)
    draw_rectangle_lines(handle_x, handle_y, handle_w, handle_h, BLACK)

    return value

# --- Scene helpers (usadas para (re)crear escenas) ---
def make_scene(scene_id: int, color: Color) -> Scene:
    size = Vector2(SCENE_W, SCENE_H)
    spawn = Vector2(SCENE_W * 0.5, SCENE_H * 0.5)
    return Scene(scene_id, size, color, spawn)

def create_scenes() -> list[Scene]:
    return [
        make_scene(1, Color(70, 120, 200, 255)),
        make_scene(2, Color(200, 120, 70, 255)),
        make_scene(3, Color(80, 160, 110, 255)),
        make_scene(4, Color(160, 80, 160, 255)),
    ]

def scene_center(scene: Scene) -> Vector2:
    if hasattr(scene, "rect"):
        return Vector2(
            scene.rect.x + scene.rect.width * 0.5,
            scene.rect.y + scene.rect.height * 0.5,
        )
    if hasattr(scene, "size"):
        return Vector2(scene.size.x * 0.5, scene.size.y * 0.5)
    return Vector2(SCENE_W * 0.5, SCENE_H * 0.5)

# --- main ---
def main() -> None:
    global SCREEN_W, SCREEN_H, SCENE_W, SCENE_H

    # inicializar ventana con la resolución por defecto
    init_window(SCREEN_W, SCREEN_H, "Juego con Menú y Sliders (UI adaptativa, escala fija)")
    set_target_fps(60)

    # estados
    STATE_MAIN_MENU = "MAIN_MENU"
    STATE_CONFIG = "CONFIG"
    STATE_PLAY = "PLAY"
    STATE_LOADING = "LOADING"  # estado para evitar dibujar el main menu durante la carga

    state = STATE_MAIN_MENU
    res_index = len(RESOLUTIONS) - 1  # default index

    # crear escenas y player
    scenes = create_scenes()
    active = 0
    player = Player(scene_center(scenes[active]))

    # cámara
    camera = Camera2D()
    camera.offset = Vector2(SCREEN_W / 2, SCREEN_H / 2)
    camera.target = Vector2(player.position.x, player.position.y)
    camera.rotation = 0.0
    camera.zoom = 1.0

    hud_controls = "1–4: escena | WASD/Flechas: mover | +/-: zoom | ESC: salir | P: menu in-game"

    # transición de carga
    TRANSITION_TIME = 3.0  # total
    FADE_TIME = 0.5
    HOLD_TIME = max(0.0, TRANSITION_TIME - 2.0 * FADE_TIME)

    loading = False
    trans_elapsed = 0.0
    target_scene: int | None = None
    swapped = False

    # optional loading image
    LOADING_IMAGE_PATH: str | None = None
    loading_texture: Texture2D | None = None
    if LOADING_IMAGE_PATH is not None:
        try:
            loading_texture = load_texture(LOADING_IMAGE_PATH)
        except Exception:
            loading_texture = None

    # sliders state (music, sfx)
    state_ui = {
        "music_volume": 0.8,      # inicial, 0..1
        "sfx_volume": 0.9,        # inicial
        "music_dragging": False,
        "sfx_dragging": False,
        "res_dropdown_open": False,  # si el desplegable de resoluciones está abierto
    }

    ingame_menu_open = False

    # cuando iniciamos una carga guardamos a qué estado queremos ir después
    post_load_state = STATE_PLAY  # por defecto si se inicia desde Main Menu -> Play

    while not window_should_close():
        dt = get_frame_time()

        # --- Input global para abrir menú in-game (solo si estamos jugando) ---
        if state == STATE_PLAY and is_key_pressed(KEY_P):
            ingame_menu_open = not ingame_menu_open

        # ESC behavior
        if is_key_pressed(KEY_ESCAPE):
            if state == STATE_MAIN_MENU:
                break
            elif state == STATE_CONFIG:
                state = STATE_MAIN_MENU
                state_ui["res_dropdown_open"] = False
            elif state == STATE_PLAY:
                if ingame_menu_open:
                    ingame_menu_open = False
                else:
                    ingame_menu_open = True
            elif state == STATE_LOADING:
                # no cancelar loading con ESC para evitar estados inconsistentes
                pass

        # --- Game updates (solo si estamos en PLAY y no estamos en overlay) ---
        if state == STATE_PLAY and not loading and not ingame_menu_open:
            move = Input.get_move_axis()
            player.update(move, dt)

            # Zoom +/- y límites
            if is_key_down(KEY_EQUAL) or is_key_down(KEY_KP_ADD):
                camera.zoom += 1.0 * dt
            if is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT):
                camera.zoom -= 1.0 * dt
            camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, camera.zoom))

            camera.target = Vector2(player.position.x, player.position.y)

        # --- Hotkeys para cambiar escena rápido (cuando estamos en PLAY) ---
        if state == STATE_PLAY and not loading and not ingame_menu_open:
            if is_key_pressed(KEY_ONE) or is_key_pressed(KEY_KP_1):
                requested = 0
                if requested != active:
                    loading = True; trans_elapsed = 0.0; target_scene = requested; swapped = False
                    post_load_state = STATE_PLAY; state = STATE_LOADING
            if is_key_pressed(KEY_TWO) or is_key_pressed(KEY_KP_2):
                requested = 1
                if requested != active:
                    loading = True; trans_elapsed = 0.0; target_scene = requested; swapped = False
                    post_load_state = STATE_PLAY; state = STATE_LOADING
            if is_key_pressed(KEY_THREE) or is_key_pressed(KEY_KP_3):
                requested = 2
                if requested != active:
                    loading = True; trans_elapsed = 0.0; target_scene = requested; swapped = False
                    post_load_state = STATE_PLAY; state = STATE_LOADING
            if is_key_pressed(KEY_FOUR) or is_key_pressed(KEY_KP_4):
                requested = 3
                if requested != active:
                    loading = True; trans_elapsed = 0.0; target_scene = requested; swapped = False
                    post_load_state = STATE_PLAY; state = STATE_LOADING

        # --- Transition update ---
        if loading:
            trans_elapsed += dt
            if (not swapped) and (trans_elapsed >= FADE_TIME):
                if target_scene is not None:
                    active = target_scene
                    player.position = scene_center(scenes[active])
                    camera.target = Vector2(player.position.x, player.position.y)
                swapped = True
            if trans_elapsed >= TRANSITION_TIME:
                loading = False
                trans_elapsed = 0.0
                target_scene = None
                swapped = False
                # cambiar al estado deseado después de la carga
                state = post_load_state

        # --- DIBUJO ---
        begin_drawing()
        clear_background(RAYWHITE)

        # Compute UI sizes from window size (LINEAR fixed scaling)
        left_margin = int(SCREEN_W * LEFT_MARGIN_RATIO)
        button_w = int(SCREEN_W * BASE_BUTTON_WIDTH_RATIO)
        button_h = int(SCREEN_H * BASE_BUTTON_HEIGHT_RATIO)
        main_button_w = int(SCREEN_W * MAIN_BASE_BUTTON_WIDTH_RATIO)
        main_button_h = int(SCREEN_H * MAIN_BASE_BUTTON_HEIGHT_RATIO)
        slider_w = int(SCREEN_W * SLIDER_WIDTH_RATIO)
        slider_h = int(SCREEN_H * SLIDER_HEIGHT_RATIO)

        # helper for font sizes (linear)
        def fsz(base): return calc_font(base)

        if state == STATE_MAIN_MENU:
            # Dibuja fondo del menú si quieres; dejamos espacio para que puedas poner un fondo posterior.
            draw_text("Mi Juego - Menú Principal", left_margin, 40, fsz(28), DARKGRAY)

            # Botones principales *pequeños* en esquina inferior izquierda
            bw = main_button_w
            bh = main_button_h
            x = left_margin
            padding_bottom = int(SCREEN_H * 0.04)
            gap = int(max(8, 12 * (SCREEN_H / REF_H)))
            start_y = SCREEN_H - padding_bottom - (bh * 3 + gap * 2)

            # Iniciar
            if draw_button_left(x, start_y + 0 * (bh + gap), bw, bh, "Iniciar", font_size=fsz(20)):
                # iniciar la carga -> luego entrar a PLAY
                loading = True
                trans_elapsed = 0.0
                target_scene = active
                swapped = False
                post_load_state = STATE_PLAY
                state = STATE_LOADING  # evita dibujar MAIN_MENU mientras carga

            # Configuración
            if draw_button_left(x, start_y + 1 * (bh + gap), bw, bh, "Configuración", font_size=fsz(20)):
                state = STATE_CONFIG

            # Salir
            if draw_button_left(x, start_y + 2 * (bh + gap), bw, bh, "Salir", font_size=fsz(20)):
                break

            # consejo para el fondo (derecha del menú)
            draw_text("Aquí irá la imagen/fondo del menú.", left_margin, start_y - 30, fsz(14), GRAY)

        elif state == STATE_CONFIG:
            # Cabecera
            draw_text("Configuración", left_margin, 28, fsz(28), DARKGRAY)
            draw_text("Resolución", left_margin, 68, fsz(22), DARKGRAY)

            # Left-aligned controls block start Y
            block_x = left_margin
            block_y = 110
            gap_y = int(max(8, 12 * (SCREEN_H / REF_H)))

            # Button que despliega resoluciones (actúa como dropdown)
            res_btn_w = button_w
            res_btn_h = button_h
            label = f"Resolución: {RESOLUTIONS[res_index][0]} × {RESOLUTIONS[res_index][1]}"
            hovered, clicked = button_left_rect(block_x, block_y, res_btn_w, res_btn_h, label, font_size=fsz(20))
            if clicked:
                state_ui["res_dropdown_open"] = not state_ui["res_dropdown_open"]

            # si desplegado, listar las resoluciones debajo (left-aligned)
            if state_ui["res_dropdown_open"]:
                for i, (w, h) in enumerate(RESOLUTIONS):
                    item_y = block_y + (i + 1) * (res_btn_h + 6)
                    text_label = f"{w} × {h}"
                    hovered_item, clicked_item = button_left_rect(block_x, item_y, res_btn_w, res_btn_h, text_label, font_size=fsz(18))
                    if clicked_item:
                        res_index = i
                        state_ui["res_dropdown_open"] = False

            # sliders: Música y Efectos (posicionados debajo)
            sl_start_y = block_y + (len(RESOLUTIONS) + 1) * (res_btn_h + 6) if state_ui["res_dropdown_open"] else block_y + (res_btn_h + 2 * gap_y)
            # Música label + slider
            draw_text("Volumen Música", block_x, sl_start_y, fsz(20), DARKGRAY)
            music_slider_x = block_x
            music_slider_y = sl_start_y + int(28 * (SCREEN_H / REF_H))
            state_ui["music_volume"] = slider_horizontal(music_slider_x, music_slider_y, slider_w, max(12, int(slider_h * 2)), state_ui["music_volume"], "music_dragging", state_ui)
            # Nota: cuando integres el sistema de audio, aplica:
            # SetMusicVolume(music_obj, state_ui["music_volume"]) o similar, donde tengas el objeto `Music`.

            # Efectos label + slider
            sfx_y = music_slider_y + max(12, int(slider_h * 2)) + int(28 * (SCREEN_H / REF_H))
            draw_text("Volumen Efectos", block_x, sfx_y, fsz(20), DARKGRAY)
            sfx_slider_x = block_x
            sfx_slider_y = sfx_y + int(28 * (SCREEN_H / REF_H))
            state_ui["sfx_volume"] = slider_horizontal(sfx_slider_x, sfx_slider_y, slider_w, max(12, int(slider_h * 2)), state_ui["sfx_volume"], "sfx_dragging", state_ui)
            # Nota: cuando integres tus sonidos (Sound), ajusta su volumen con:
            # SetSoundVolume(sound_obj, state_ui["sfx_volume"]) o globalmente SetMasterVolume / similar.

            # Botones aplicar / volver (left-aligned)
            btn_w = int(button_w * 0.6)
            btn_h = button_h
            by = SCREEN_H - int(SCREEN_H * 0.06) - btn_h
            if draw_button_left(block_x, by, btn_w, btn_h, "Aplicar", font_size=fsz(20)):
                new_w, new_h = RESOLUTIONS[res_index]
                SCREEN_W, SCREEN_H = new_w, new_h
                SCENE_W, SCENE_H = SCREEN_W, SCREEN_H
                set_window_size(SCREEN_W, SCREEN_H)
                # Recreate scenes and reposition player/camera to handle new window size
                scenes = create_scenes()
                player.position = scene_center(scenes[active])
                camera.offset = Vector2(SCREEN_W / 2, SCREEN_H / 2)
                camera.target = Vector2(player.position.x, player.position.y)
            if draw_button_left(block_x + btn_w + int(12 * (SCREEN_W / REF_H)), by, btn_w, btn_h, "Volver", font_size=fsz(20)):
                state = STATE_MAIN_MENU
                state_ui["res_dropdown_open"] = False

        elif state == STATE_PLAY:
            # dibujar escena y jugador (con cámara)
            _begin_mode_2d(camera)
            scenes[active].draw()
            player.draw()
            _end_mode_2d()

            # HUD (left-aligned)
            draw_text("En juego - presiona P para menú", left_margin, 10, fsz(18), DARKGRAY)

            # In-game menu overlay
            if ingame_menu_open:
                draw_rectangle(0, 0, SCREEN_W, SCREEN_H, Color(0, 0, 0, 160))
                # menú left-aligned but centered vertically
                bw = button_w
                bh = button_h
                x = left_margin
                cy = SCREEN_H // 2 - (bh * 3 + int(12 * (SCREEN_H / REF_H)) * 2) // 2
                gap = int(max(8, 12 * (SCREEN_H / REF_H)))
                if draw_button_left(x, cy + 0 * (bh + gap), bw, bh, "Reanudar", font_size=fsz(20)):
                    ingame_menu_open = False
                if draw_button_left(x, cy + 1 * (bh + gap), bw, bh, "Menu Principal", font_size=fsz(20)):
                    state = STATE_MAIN_MENU
                    ingame_menu_open = False
                if draw_button_left(x, cy + 2 * (bh + gap), bw, bh, "Salir", font_size=fsz(20)):
                    break

        elif state == STATE_LOADING:
            # Si estamos en STATE_LOADING preferimos no dibujar el main menu detrás.
            clear_background(BLACK)

        # --- Overlay de carga (si loading está activo) ---
        if loading:
            # Calcula alpha del fade (0..255)
            if trans_elapsed < FADE_TIME:
                alpha = int((trans_elapsed / FADE_TIME) * 255)  # fade-out: 0 -> 255
            elif trans_elapsed < FADE_TIME + HOLD_TIME:
                alpha = 255  # hold
            elif trans_elapsed < FADE_TIME + HOLD_TIME + FADE_TIME:
                t = (trans_elapsed - FADE_TIME - HOLD_TIME) / FADE_TIME
                alpha = int((1.0 - t) * 255)  # fade-in: 255 -> 0
            else:
                alpha = 0
            alpha = max(0, min(255, alpha))

            draw_rectangle(0, 0, SCREEN_W, SCREEN_H, Color(30, 30, 30, alpha))

            if loading_texture is not None:
                tex_w = loading_texture.width
                tex_h = loading_texture.height
                # fit inside screen (puedes cambiar a cover usando max())
                scale = min(SCREEN_W / tex_w, SCREEN_H / tex_h)
                draw_w = int(tex_w * scale)
                draw_h = int(tex_h * scale)
                draw_x = (SCREEN_W - draw_w) // 2
                draw_y = (SCREEN_H - draw_h) // 2
                draw_texture_ex(loading_texture, Vector2(draw_x, draw_y), 0.0, scale, Color(255, 255, 255, alpha))
            else:
                draw_text("Cargando...", SCREEN_W // 2 - 70, SCREEN_H // 2 - 10, fsz(28), Color(220, 220, 220, max(120, alpha)))

        end_drawing()

        # --- NOTAS SOBRE AUDIO (dentro del loop o cuando sea apropiado):
        # - Cuando tengas objetos de audio:
        #     - Para música (streaming), aplica el volumen global o de la instancia:
        #         SetMusicVolume(music_obj, state_ui["music_volume"])  # o set_music_volume(...) según binding
        #     - Para efectos (Sound), ajusta por instancia o global: SetSoundVolume(sound_obj, state_ui["sfx_volume"])
        # - Llama a esas funciones justo después de cargar los objetos `Music`/`Sound`
        #   o periódicamente si quieres que los cambios sean inmediatos cuando mueves los sliders.

    # cleanup
    if loading_texture is not None:
        unload_texture(loading_texture)
    close_window()

if __name__ == "__main__":
    main()
