"""Loop principal del juego con escenas independientes, jugador y cámara 2D."""

from __future__ import annotations

import raylibpy as rl

from classes import Player, Scene
import Input  # movimiento WASD/flechas

SCREEN_W, SCREEN_H = 960, 540
SCENE_W, SCENE_H = SCREEN_W, SCREEN_H
MIN_ZOOM, MAX_ZOOM = 0.35, 3.0

# Wrappers "lint-safe" por diferencias de nombre en bindings
_begin_mode_2d = getattr(rl, "begin_mode_2d", getattr(rl, "begin_mode2d"))
_end_mode_2d = getattr(rl, "end_mode_2d", getattr(rl, "end_mode2d"))


def make_scene(scene_id: int, color: rl.Color) -> Scene:
    """Crea una `Scene` usando la firma (id, size, color, spawn)."""
    size = rl.Vector2(SCENE_W, SCENE_H)
    spawn = rl.Vector2(SCENE_W * 0.5, SCENE_H * 0.5)
    return Scene(scene_id, size, color, spawn)


def create_scenes() -> list[Scene]:
    """Crea las 4 escenas de ejemplo."""
    return [
        make_scene(1, rl.Color(70, 120, 200, 255)),
        make_scene(2, rl.Color(200, 120, 70, 255)),
        make_scene(3, rl.Color(80, 160, 110, 255)),
        make_scene(4, rl.Color(160, 80, 160, 255)),
    ]


def scene_center(scene: Scene) -> rl.Vector2:
    """Centro geométrico de la escena, compatible con distintas representaciones."""
    if hasattr(scene, "rect"):
        return rl.Vector2(
            scene.rect.x + scene.rect.width * 0.5,
            scene.rect.y + scene.rect.height * 0.5,
        )
    if hasattr(scene, "size"):
        return rl.Vector2(scene.size.x * 0.5, scene.size.y * 0.5)
    return rl.Vector2(SCENE_W * 0.5, SCENE_H * 0.5)


def handle_scene_hotkeys(active_idx: int) -> int:
    """Devuelve el índice de escena según teclas 1–4 (fila superior o numérico)."""
    if rl.is_key_pressed(rl.KEY_ONE) or rl.is_key_pressed(rl.KEY_KP_1):
        return 0
    if rl.is_key_pressed(rl.KEY_TWO) or rl.is_key_pressed(rl.KEY_KP_2):
        return 1
    if rl.is_key_pressed(rl.KEY_THREE) or rl.is_key_pressed(rl.KEY_KP_3):
        return 2
    if rl.is_key_pressed(rl.KEY_FOUR) or rl.is_key_pressed(rl.KEY_KP_4):
        return 3
    return active_idx


def main() -> None:
    """Punto de entrada: movimiento, zoom y cambio de escena."""
    rl.init_window(SCREEN_W, SCREEN_H, "Escenas independientes (1–4) + zoom")
    rl.set_target_fps(60)

    scenes = create_scenes()
    active = 0

    # Jugador empieza centrado en la escena activa
    player = Player(scene_center(scenes[active]))

    # Cámara 2D nativa
    camera = rl.Camera2D()
    camera.offset = rl.Vector2(SCREEN_W / 2, SCREEN_H / 2)
    camera.target = rl.Vector2(player.position.x, player.position.y)
    camera.rotation = 0.0
    camera.zoom = 1.0

    hud_controls = "1–4: escena | WASD/Flechas: mover | +/-: zoom | ESC: salir"

    while not rl.window_should_close():
        dt = rl.get_frame_time()

        # Cambiar de escena
        new_index = handle_scene_hotkeys(active)
        if new_index != active:
            active = new_index
            player.position = scene_center(scenes[active])

        # Movimiento del jugador
        move = Input.get_move_axis()
        player.update(move, dt)

        # Zoom +/- y límites
        if rl.is_key_down(rl.KEY_EQUAL) or rl.is_key_down(rl.KEY_KP_ADD):
            camera.zoom += 1.0 * dt
        if rl.is_key_down(rl.KEY_MINUS) or rl.is_key_down(rl.KEY_KP_SUBTRACT):
            camera.zoom -= 1.0 * dt
        camera.zoom = max(MIN_ZOOM, min(MAX_ZOOM, camera.zoom))

        # Cámara sigue al jugador
        camera.target = rl.Vector2(player.position.x, player.position.y)

        # Dibujo
        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)

        _begin_mode_2d(camera)  # evita que Pylint se queje de atributo no existente
        # if hasattr(scenes[active], "update"): scenes[active].update(dt)
        scenes[active].draw()
        player.draw()
        _end_mode_2d()

        rl.draw_text(hud_controls, 10, 10, 18, rl.DARKGRAY)
        rl.draw_text(f"Escena activa: {active + 1}", 10, 34, 18, rl.DARKGRAY)
        rl.draw_text(f"Zoom: {camera.zoom:.2f}", 10, 58, 18, rl.DARKGRAY)

        rl.end_drawing()

    rl.close_window()


if __name__ == "__main__":
    main()
