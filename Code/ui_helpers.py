# ui_helpers.py

from __future__ import annotations
from typing import Tuple, Dict, Any
from pyray import *
import math

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

# Ajuste global: reducción ligera del tamaño visual por defecto
_GLOBAL_SHRINK = 0.92

# Reducción específica para la altura de botones (~10% más pequeños)
BUTTON_HEIGHT_SHRINK = 0.90

def measure(text: str, size: int) -> int:
    """Wrapper para medir texto."""
    return measure_text(text, size)


def calc_font(screen_h: int, base_font: int) -> int:
    """Escalado no lineal (tipo log) del tamaño de fuente según la altura de la ventana.

    - Se mantiene compatibilidad con la API anterior (recibe base_font y devuelve un int).
    - Usa logaritmos para que el crecimiento/encogimiento sea más suave que el escalado lineal
      y además aplica una ligera reducción global para "hacer todo un poco más pequeño".
    - Se garantizan mínimos/ máximos razonables para que no explote en tamaños extremos.
    """
    # protección
    screen_h = max(1.0, float(screen_h))
    scale = screen_h / REF_H

    # factor logarítmico: cuando scale==1 => factor==1
    # cuando scale>1 -> 1 + 0.6*log(scale) (crece pero suavemente)
    # cuando scale<1 -> 1 + 0.6*log(scale) (decrece suavemente)
    factor = 1.0 + 0.6 * math.log(scale)

    # clamp para evitar tamaños extremos
    factor = max(0.65, min(1.35, factor))

    # aplicamos pequeña reducción global para textos "un poco más pequeños" en general
    factor *= _GLOBAL_SHRINK

    return max(12, int(base_font * factor))


def _mouse_in_rect(x: int, y: int, w: int, h: int) -> bool:
    m = get_mouse_position()
    mx, my = int(m.x), int(m.y)
    return (mx >= x and mx <= x + w and my >= y and my <= y + h)


def draw_button_left(x: int, y: int, w: int, h: int, text: str, font_size: int = 22) -> bool:
    """Dibuja un botón alineado a la izquierda. Retorna True si fue clicado.

    Ajustes realizados:
    - Limitamos el font_size máximo para que nunca sea mayor que una fracción del alto
      del botón (evita que el texto "salte" fuera del botón).
    - El tamaño de fuente que se pasa se respeta pero se recorta si es demasiado grande.
    - El centrado vertical usa el font_size efectivo.
    """
    hovered = _mouse_in_rect(x, y, w, h)
    bg = SKYBLUE if hovered else DARKGRAY
    txt_color = BLACK if hovered else WHITE

    draw_rectangle(x, y, w, h, bg)
    draw_rectangle_lines(x, y, w, h, BLACK)

    # No permitir que el texto exceda del botón: tomar como máximo 70% de la altura del botón
    max_font = max(10, int(h * 0.70))
    eff_font = min(font_size, max_font)

    draw_text(text, x + 8, y + (h - eff_font) // 2, eff_font, txt_color)

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


def _ui_nonlinear_factor(screen_h: int) -> float:
    """Devuelve un factor no lineal (log) basado en la altura de la pantalla.

    Usado para escalar dimensiones de UI (anchos/altos de botones, sliders) de forma menos agresiva
    que el escalado lineal clásico. Esto evita que los controles crezcan/desaparezcan y ayuda a que
    no choquen entre sí en tamaños extremos.
    """
    screen_h = max(1.0, float(screen_h))
    scale = screen_h / REF_H
    factor = 1.0 + 0.5 * math.log(scale)
    factor = max(0.7, min(1.3, factor))
    factor *= _GLOBAL_SHRINK
    return factor


def calculate_ui_dimensions(screen_w: int, screen_h: int) -> dict[str, int]:
    """Calcula las dimensiones de los elementos UI según el tamaño de la ventana.

    Cambios:
    - Aplicamos un factor no lineal para que medidas como button_w/button_h escalen suavemente.
    - Añadimos mínimos razonables para evitar solapamientos en pantallas pequeñas.
    - Reducimos la altura de los botones en un ~10% aplicando BUTTON_HEIGHT_SHRINK.
    """
    nf = _ui_nonlinear_factor(screen_h)

    # dimensiones base (se comprimen con nf)
    btn_w = int(screen_w * BASE_BUTTON_WIDTH_RATIO * nf)
    # aplicada reducción específica para altura de botones (~10% más pequeños)
    btn_h = max(26, int(screen_h * BASE_BUTTON_HEIGHT_RATIO * nf * BUTTON_HEIGHT_SHRINK))

    main_btn_w = int(screen_w * MAIN_BASE_BUTTON_WIDTH_RATIO * nf)
    main_btn_h = max(26, int(screen_h * MAIN_BASE_BUTTON_HEIGHT_RATIO * nf * BUTTON_HEIGHT_SHRINK))

    slider_w = max(80, int(screen_w * SLIDER_WIDTH_RATIO * nf))
    slider_h = max(14, int(screen_h * SLIDER_HEIGHT_RATIO * nf))

    return {
        "left_margin": int(screen_w * LEFT_MARGIN_RATIO),
        "button_w": btn_w,
        "button_h": btn_h,
        "main_button_w": main_btn_w,
        "main_button_h": main_btn_h,
        "slider_w": slider_w,
        "slider_h": slider_h,
    }
