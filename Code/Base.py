"""Loop principal del juego con escenas independientes, jugador y cámara 2D.
   Agregado: fade out -> switch -> fade in entre escenas (3s por defecto).
   Recuadro de carga ahora CUBRE TODA LA PANTALLA (puede mostrar una imagen).
"""

from __future__ import annotations

from pyray import *
from Classes import Player, Scene
import Input  # movimiento WASD/flechas

SCREEN_W, SCREEN_H = 960, 540
SCENE_W, SCENE_H = SCREEN_W, SCREEN_H
MIN_ZOOM, MAX_ZOOM = 0.35, 3.0

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

def handle_scene_hotkeys(active_idx: int) -> int:
    if is_key_pressed(KEY_ONE) or is_key_pressed(KEY_KP_1):
        return 0
    if is_key_pressed(KEY_TWO) or is_key_pressed(KEY_KP_2):
        return 1
    if is_key_pressed(KEY_THREE) or is_key_pressed(KEY_KP_3):
        return 2
    if is_key_pressed(KEY_FOUR) or is_key_pressed(KEY_KP_4):
        return 3
    return active_idx

def main() -> None:
    init_window(SCREEN_W, SCREEN_H, "Escenas independientes (1–4) + fade entre escenas (recuadro full-screen)")
    set_target_fps(60)

    scenes = create_scenes()
    active = 0

    # Jugador empieza centrado en la escena activa
    player = Player(scene_center(scenes[active]))

    # Cámara 2D nativa
    camera = Camera2D()
    camera.offset = Vector2(SCREEN_W / 2, SCREEN_H / 2)
    camera.target = Vector2(player.position.x, player.position.y)
    camera.rotation = 0.0
    camera.zoom = 1.0

    hud_controls = "1–4: escena | WASD/Flechas: mover | +/-: zoom | ESC: salir"

    # --- Estado para transición con fade ---
    TRANSITION_TIME = 3.0  # segundos totales (fade out + hold + fade in)
    FADE_TIME = 0.5        # duración de cada fade (fade-out y fade-in)
    HOLD_TIME = max(0.0, TRANSITION_TIME - 2.0 * FADE_TIME)  # tiempo en el que la pantalla queda al 100% alpha
    loading = False
    trans_elapsed = 0.0
    target_scene: int | None = None
    swapped = False  # para hacer el cambio justo después del fade-out

    # --- Opcional: carga una imagen para mostrar durante la carga ---
    LOADING_IMAGE_PATH: str | None = None  # ej: "assets/logo.png"
    loading_texture: Texture2D | None = None
    if LOADING_IMAGE_PATH is not None:
        try:
            loading_texture = load_texture(LOADING_IMAGE_PATH)
        except Exception:
            loading_texture = None

    while not window_should_close():
        dt = get_frame_time()

        # Manejo del pedido de cambio de escena: inicia la transición (si no ya en transición)
        requested = handle_scene_hotkeys(active)
        if (requested != active) and (not loading):
            loading = True
            trans_elapsed = 0.0
            target_scene = requested
            swapped = False

        # ESC siempre cierra
        if is_key_pressed(KEY_ESCAPE):
            break

        # Actualización normal (congelada durante la transición)
        if not loading:
            # Movimiento del jugador
            move = Input.get_move_axis()
            player.update(move, dt)

            # Zoom +/- y límites
            if is_key_down(KEY_EQUAL) or is_key_down(KEY_KP_ADD):
                camera.zoom += 1.0 * dt
            if is_key_down(KEY_MINUS) or is_key_down(KEY_KP_SUBTRACT):
                camera.zoom -= 1.0 * dt
            camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, camera.zoom))

            # Cámara sigue al jugador
            camera.target = Vector2(player.position.x, player.position.y)
        else:
            # avanzamos el temporizador de transición
            trans_elapsed += dt

            # cuando termina el fade-out (FADE_TIME) hacemos el swap una vez
            if (not swapped) and (trans_elapsed >= FADE_TIME):
                if target_scene is not None:
                    active = target_scene
                    player.position = scene_center(scenes[active])
                    camera.target = Vector2(player.position.x, player.position.y)
                swapped = True

            # si la transición completa (fade-out + hold + fade-in) termina, reiniciamos estado
            if trans_elapsed >= TRANSITION_TIME:
                loading = False
                trans_elapsed = 0.0
                target_scene = None
                swapped = False

        # --- Dibujo ---
        begin_drawing()
        clear_background(RAYWHITE)

        # Dibuja la escena y jugador normalmente (aunque la pantalla se cubrirá por el fade)
        begin_mode_2d(camera)
        scenes[active].draw()
        player.draw()
        end_mode_2d()

        # HUD
        draw_text(hud_controls, 10, 10, 18, DARKGRAY)
        draw_text(f"Escena activa: {active + 1}", 10, 34, 18, DARKGRAY)
        draw_text(f"Zoom: {camera.zoom:.2f}", 10, 58, 18, DARKGRAY)

        # Si está en transición, dibujar fade + recuadro FULL-SCREEN (para imagen posterior)
        if loading:
            # Calcula alpha del fade (0..255)
            if trans_elapsed < FADE_TIME:
                # fade-out: 0 -> 255
                alpha = int((trans_elapsed / FADE_TIME) * 255)
            elif trans_elapsed < FADE_TIME + HOLD_TIME:
                # hold: 255
                alpha = 255
            elif trans_elapsed < FADE_TIME + HOLD_TIME + FADE_TIME:
                # fade-in: 255 -> 0
                t = (trans_elapsed - FADE_TIME - HOLD_TIME) / FADE_TIME
                alpha = int((1.0 - t) * 255)
            else:
                alpha = 0
            alpha = max(0, min(255, alpha))

            # RECUADRO FULL-SCREEN: fondo (negro con alpha calculado)
            draw_rectangle(0, 0, SCREEN_W, SCREEN_H, Color(30, 30, 30, alpha))

            # Si hay textura cargada, dibujarla centrada y escalada para FIT dentro de la pantalla manteniendo aspect ratio
            if loading_texture is not None:
                tex_w = loading_texture.width
                tex_h = loading_texture.height
                # escala para que quepa en la pantalla sin deformar (fit inside)
                scale = min(SCREEN_W / tex_w, SCREEN_H / tex_h)
                draw_w = int(tex_w * scale)
                draw_h = int(tex_h * scale)
                draw_x = (SCREEN_W - draw_w) // 2
                draw_y = (SCREEN_H - draw_h) // 2
                draw_texture_ex(loading_texture, Vector2(draw_x, draw_y), 0.0, scale, Color(255, 255, 255, alpha))
            else:
                # Texto placeholder centrado
                draw_text("Cargando...", SCREEN_W // 2 - 70, SCREEN_H // 2 - 10, 28, Color(220, 220, 220, max(120, alpha)))

        end_drawing()

    # Liberar textura si se cargó
    if loading_texture is not None:
        unload_texture(loading_texture)

    close_window()

if __name__ == "__main__":
    main()