from pyray import *
from typing import NamedTuple

# Usaremos un NamedTuple para devolver la intención del jugador de forma clara.
# Podrías usar un diccionario o una clase, pero NamedTuple es más ligero.
class PlayerInput(NamedTuple):
    move_vector: Vector2
    is_sprinting: bool

def get_player_input() -> PlayerInput:
    """Devuelve el vector de movimiento normalizado y el estado de sprint."""
    x = 0
    y = 0
    
    # 1. Detección de movimiento
    if is_key_down(KEY_A) or is_key_down(KEY_LEFT):
        x -= 1
    if is_key_down(KEY_D) or is_key_down(KEY_RIGHT):
        x += 1
    if is_key_down(KEY_W) or is_key_down(KEY_UP):
        y -= 1
    if is_key_down(KEY_S) or is_key_down(KEY_DOWN):
        y += 1
        
    # 2. Detección de Sprint (se requiere movimiento y la tecla SHIFT)
    is_moving = (x != 0 or y != 0)
    is_sprinting = is_moving and (is_key_down(KEY_LEFT_SHIFT) or is_key_down(KEY_RIGHT_SHIFT))

    move_vec = Vector2(0.0, 0.0)
    if is_moving:
        move_vec = Vector2(float(x), float(y))
        length = ((move_vec.x * move_vec.x) + (move_vec.y * move_vec.y)) ** 0.5
        
        if length > 1e-6:
            move_vec.x /= length
            move_vec.y /= length

    return PlayerInput(move_vec, is_sprinting)