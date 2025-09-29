# input_handler.py

from pyray import *

def get_move_axis() -> Vector2:
    """Devuelve vector de movimiento normalizado en ejes X/Y según WASD o flechas."""
    x = 0
    y = 0

    if is_key_down(KEY_A) or is_key_down(KEY_LEFT):
        x -= 1
    if is_key_down(KEY_D) or is_key_down(KEY_RIGHT):
        x += 1
    if is_key_down(KEY_W) or is_key_down(KEY_UP):
        y -= 1
    if is_key_down(KEY_S) or is_key_down(KEY_DOWN):
        y += 1

    if x != 0 or y != 0:
        v = Vector2(float(x), float(y))
        length = ((v.x * v.x) + (v.y * v.y)) ** 0.5
        # Evitar división por cero, aunque el chequeo `x != 0 or y != 0` ya lo hace
        if length > 1e-6:
            v.x /= length
            v.y /= length
            return v
    return Vector2(0.0, 0.0)