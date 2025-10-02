# ui_helpers.py
import pyray as rl

def draw_panel(rect, title: str = "", scale: float = 1.0):
    x, y, w, h = rect
    rl.draw_rectangle_rounded(rl.Rectangle(x, y, w, h), 0.04, 12, rl.fade(rl.BLACK, 0.6))
    rl.draw_rectangle_rounded_lines(rl.Rectangle(x, y, w, h), 0.04, 12, 2, rl.RAYWHITE)
    if title:
        rl.draw_text(title, int(x + 16 * scale), int(y + 14 * scale), int(22 * scale), rl.RAYWHITE)

def draw_label(text: str, pos, font_size: int):
    rl.draw_text(text, int(pos[0]), int(pos[1]), font_size, rl.RAYWHITE)

def center_rect_in_screen(width: int, height: int):
    sw = rl.get_screen_width()
    sh = rl.get_screen_height()
    return int(sw/2 - width/2), int(sh/2 - height/2), width, height
