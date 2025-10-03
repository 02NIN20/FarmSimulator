# ui_helpers.py

from __future__ import annotations
from typing import Tuple, Dict, Any
from pyray import *

# Valores por defecto
REF_H = 540.0

# Ratios de UI
LEFT_MARGIN_RATIO = 0.05
BASE_BUTTON_WIDTH_RATIO = 0.26
BASE_BUTTON_HEIGHT_RATIO = 0.085
MAIN_BASE_BUTTON_WIDTH_RATIO = 0.18
MAIN_BASE_BUTTON_HEIGHT_RATIO = 0.07
SLIDER_WIDTH_RATIO = 0.28
SLIDER_HEIGHT_RATIO = 0.04

def measure(text: str, size: int) -> int:
    """Wrapper para medir texto."""
    return measure_text(text, size)

def calc_font(screen_h: int, base_font: int) -> int:
    """Escalado lineal del tamaño de fuente según la altura de la ventana."""
    return max(12, int(base_font * (screen_h / REF_H)))

def _mouse_in_rect(x: int, y: int, w: int, h: int) -> bool:
    m = get_mouse_position()
    mx, my = int(m.x), int(m.y)
    return (mx >= x and mx <= x + w and my >= y and my <= y + h)

def draw_button_left(x: int, y: int, w: int, h: int, text: str, font_size: int = 22) -> bool:
    """Dibuja un botón alineado a la izquierda. Retorna True si fue clicado."""
    hovered = _mouse_in_rect(x, y, w, h)
    bg = SKYBLUE if hovered else DARKGRAY
    txt_color = BLACK if hovered else WHITE

    draw_rectangle(x, y, w, h, bg)
    draw_rectangle_lines(x, y, w, h, BLACK)
    draw_text(text, x + 8, y + (h - font_size) // 2, font_size, txt_color)

    clicked = hovered and is_mouse_button_pressed(MOUSE_BUTTON_LEFT)
    return clicked

def button_left_rect(x: int, y: int, w: int, h: int, text: str, font_size: int = 22) -> Tuple[Rectangle, bool]:
    """Como draw_button_left pero devuelve también el rectángulo de dibujo."""
    clicked = draw_button_left(x, y, w, h, text, font_size)
    return Rectangle(x, y, w, h), clicked

def slider_horizontal(x: int, y: int, w: int, h: int, value: float, dragging_flag: str, state: Dict[str, Any]) -> float:
    """Dibuja un slider horizontal [0..1] y devuelve el nuevo valor.
    Usa state[dragging_flag] para arrastre continuo.
    """
    # Inicializa flag si falta
    if dragging_flag not in state:
        state[dragging_flag] = False

    # Clamp valor
    value = max(0.0, min(1.0, float(value)))

    # Pista
    track_color = Color(210, 210, 210, 255)
    draw_rectangle(x, y + h // 2 - 3, w, 6, track_color)
    draw_rectangle_lines(x, y, w, h, BLACK)

    # Handle
    handle_w = max(14, h)
    handle_h = h
    handle_x = x + int(value * (w - handle_w))
    handle_y = y
    draw_rectangle(handle_x, handle_y, handle_w, handle_h, GRAY)
    draw_rectangle_lines(handle_x, handle_y, handle_w, handle_h, BLACK)

    # Entrada de ratón
    mouse = get_mouse_position()
    mx, my = int(mouse.x), int(mouse.y)

    over_track = (mx >= x and mx <= x + w and my >= y and my <= y + h)
    over_handle = (mx >= handle_x and mx <= handle_x + handle_w and my >= handle_y and my <= handle_y + handle_h)

    # Comienza arrastre
    if is_mouse_button_pressed(MOUSE_BUTTON_LEFT) and (over_handle or over_track):
        state[dragging_flag] = True

    # Termina arrastre
    if state[dragging_flag] and is_mouse_button_released(MOUSE_BUTTON_LEFT):
        state[dragging_flag] = False

    # Actualiza valor si arrastrando
    if state[dragging_flag]:
        # Posición relativa del mouse dentro del slider
        rel = (mx - x - handle_w / 2) / max(1, (w - handle_w))
        value = max(0.0, min(1.0, rel))

    return value

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
