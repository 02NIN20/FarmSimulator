# ui_helpers.py

from __future__ import annotations
from pyray import *

# Valores por defecto (se usan para escalar la UI)
REF_H = 540.0

# --- UI layout base ratios (relativos, lineales) ---
LEFT_MARGIN_RATIO = 0.05         # margen izquierdo relativo al ancho
BASE_BUTTON_WIDTH_RATIO = 0.26   # ancho base relativo al ancho de la ventana
BASE_BUTTON_HEIGHT_RATIO = 0.085 # alto base relativo al alto de la ventana
MAIN_BASE_BUTTON_WIDTH_RATIO = 0.18
MAIN_BASE_BUTTON_HEIGHT_RATIO = 0.07
SLIDER_WIDTH_RATIO = 0.28
SLIDER_HEIGHT_RATIO = 0.04

def measure(text: str, size: int) -> int:
    """Wrapper para medir texto."""
    return measure_text(text, size)

def calc_font(screen_h: int, base_font: int) -> int:
    """Escalado lineal del tamaño de fuente según la altura de la ventana (base en REF_H)."""
    return max(12, int(base_font * (screen_h / REF_H)))

# Las funciones de UI ahora toman screen_w/screen_h para calcular tamaños.
# Sin embargo, las funciones de dibujo (draw_button_left, button_left_rect, slider_horizontal)
# trabajan con coordenadas y dimensiones pre-calculadas por el llamador (Game).

def draw_button_left(x: int, y: int, w: int, h: int, text: str, font_size: int = 22) -> bool:
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

def button_left_rect(x: int, y: int, w: int, h: int, text: str, font_size: int = 22) -> tuple[bool, bool]:
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
    
    # Solo iniciar el drag si el mouse está sobre el handle o el track Y no estás arrastrando otro slider
    if mouse_pressed and (hovered_handle or hovered_track):
        # Asume que si 'dragging' en el dict es True, ya es este slider
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

# Helpers para el cálculo de dimensiones en la clase Game
def calculate_ui_dimensions(screen_w: int, screen_h: int) -> dict[str, int]:
    """Calcula las dimensiones de los elementos UI según el tamaño de la ventana."""
    return {
        "left_margin": int(screen_w * LEFT_MARGIN_RATIO),
        "button_w": int(screen_w * BASE_BUTTON_WIDTH_RATIO),
        "button_h": int(screen_h * BASE_BUTTON_HEIGHT_RATIO),
        "main_button_w": int(screen_w * MAIN_BASE_BUTTON_WIDTH_RATIO),
        "main_button_h": int(screen_h * MAIN_BASE_BUTTON_HEIGHT_RATIO),
        "slider_w": int(screen_w * SLIDER_WIDTH_RATIO),
        "slider_h": int(screen_h * SLIDER_HEIGHT_RATIO),
    }