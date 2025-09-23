"""Loop principal: escenas independientes + jugador + zoom (sin CameraController).
Usa directamente raylib.Camera2D para evitar errores de atributos faltantes.
"""
import raylibpy as rl

from Classes import Player, Scene
import Input

SCREEN_W, SCREEN_H = 960, 540
SCENE_W, SCENE_H = SCREEN_W, SCREEN_H  # cada escena llena la pantalla
MIN_ZOOM, MAX_ZOOM = 0.35, 3.0


def create_scenes():
    """Crea 4 escenas del tamaño de pantalla, cada una con un color distinto."""
    return [
        Scene(1, rl.Rectangle(0, 0, SCENE_W, SCENE_H), rl.Color(70, 120, 200, 255)),
        Scene(2, rl.Rectangle(0, 0, SCENE_W, SCENE_H), rl.Color(200, 120, 70, 255)),
        Scene(3, rl.Rectangle(0, 0, SCENE_W, SCENE_H), rl.Color(80, 160, 110, 255)),
        Scene(4, rl.Rectangle(0, 0, SCENE_W, SCENE_H), rl.Color(160, 80, 160, 255)),
    ]


def scene_center(scene: Scene) -> rl.Vector2:
    """Centro geométrico de una escena (usando su rect)."""
    return rl.Vector2(scene.rect.x + scene.rect.width * 0.5,
                      scene.rect.y + scene.rect.height * 0.5)


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


def main():
    rl.init_window(SCREEN_W, SCREEN_H, "Escenas independientes (1–4) + zoom")
    rl.set_target_fps(60)

    scenes = create_scenes()
    active = 0

    # Jugador empieza centrado en la escena activa
    player = Player(scene_center(scenes[active]))

    # Cámara 2D nativa de raylib
    camera = rl.Camera2D()
    camera.offset = rl.Vector2(SCREEN_W / 2, SCREEN_H / 2)
    camera.target = rl.Vector2(player.position.x, player.position.y)
    camera.rotation = 0.0
    camera.zoom = 1.0

    hud_controls = "1–4: escena | WASD/Flechas: mover | +/-: zoom | ESC: salir"

    while not rl.window_should_close():
        dt = rl.get_frame_time()

        # Cambiar de escena con 1–4
        new_index = handle_scene_hotkeys(active)
        if new_index != active:
            active = new_index
            player.position = scene_center(scenes[active])

        # Movimiento del jugador
        move = Input.get_move_axis()
        player.update(move, dt)

        # Zoom +/- (fila superior o numérico)
        if rl.is_key_down(rl.KEY_EQUAL) or rl.is_key_down(rl.KEY_KP_ADD):
            camera.zoom += 1.0 * dt
        if rl.is_key_down(rl.KEY_MINUS) or rl.is_key_down(rl.KEY_KP_SUBTRACT):
            camera.zoom -= 1.0 * dt
        # Limitar zoom
        if camera.zoom < MIN_ZOOM:
            camera.zoom = MIN_ZOOM
        if camera.zoom > MAX_ZOOM:
            camera.zoom = MAX_ZOOM

        # Cámara sigue al jugador
        camera.target = rl.Vector2(player.position.x, player.position.y)

        # Dibujo
        rl.begin_drawing()
        rl.clear_background(rl.RAYWHITE)

        rl.begin_mode_2d(camera)
        scenes[active].draw()  # solo escena activa
        player.draw()
        rl.end_mode_2d()

        rl.draw_text(hud_controls, 10, 10, 18, rl.DARKGRAY)
        rl.draw_text(f"Escena activa: {active + 1}", 10, 34, 18, rl.DARKGRAY)
        rl.draw_text(f"Zoom: {camera.zoom:.2f}", 10, 58, 18, rl.DARKGRAY)

        rl.end_drawing()

    rl.close_window()

if __name__ == "__main__":
    main()
