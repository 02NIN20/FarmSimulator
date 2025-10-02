# input_handler.py

from pyray import *
from typing import NamedTuple

# input_handler.py (or wherever PlayerInput is defined)
class PlayerInput(NamedTuple):
    move_vector: Vector2
    is_sprinting: bool
    has_destination: bool
    destination_point: Vector2

def get_player_input(current_player_position: Vector2, current_destination: Vector2, mouse_world_pos: Vector2) -> PlayerInput:
    """
    Calcula la intención del jugador (clic para mover) en coordenadas de mundo.
    """
    destination = current_destination
    
    # 1. Detección de clic derecho (para establecer un nuevo destino)
    if is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
        destination = mouse_world_pos  # Usamos la posición del mouse ya transformada a coordenadas de mundo
        
    # 2. Determinar si hay un destino y calcular el vector
    distance_to_destination = vector2_distance(current_player_position, destination)
    TOLERANCE = 5.0
    
    has_destination = distance_to_destination > TOLERANCE
    
    move_vec = Vector2(0.0, 0.0)
    
    if has_destination:
        # Vector desde la posición actual hasta el destino
        move_vec = vector2_subtract(destination, current_player_position)
        # Normalizar el vector para obtener solo la dirección
        move_vec = vector2_normalize(move_vec)
    else:
        # Si ya llegamos, aseguramos que el destino sea la posición actual para detenernos
        destination = current_player_position 

    # 3. Detección de Sprint
    is_sprinting = is_key_down(KEY_LEFT_SHIFT)
    
    return PlayerInput(move_vec, is_sprinting, has_destination, destination)