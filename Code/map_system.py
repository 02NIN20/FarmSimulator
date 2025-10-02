# map_system.py

from __future__ import annotations
from typing import List, Optional
from pyray import *

class MapSystem:
    """Sistema de mapa del mundo con selección por clic."""
    def __init__(self, total_scenes: int):
        self.is_open: bool = False
        self.total_scenes = total_scenes
        
        self.scene_colors = [
            Color(70, 120, 200, 255),   # Escena 1
            Color(200, 120, 70, 255),   # Escena 2
            Color(80, 160, 110, 255),   # Escena 3
            Color(160, 80, 160, 255),   # Escena 4
        ]
        
        # Nombres alineados a tus zonas reales
        self.scene_names = [
            "Escenario 1 — Área Local",
            "Escenario 2 — Alaska (Valle Matanuska-Susitna)",
            "Escenario 3 — Dakota del Norte (Woodworth – PPR)",
            "Escenario 4 — Michigan (Suttons Bay – Leelanau Peninsula)",
        ]

        # Geometría cacheada del grid (para handle_click)
        self._last_grid = []  # lista de (i, x, y, w, h)

    def toggle(self):
        self.is_open = not self.is_open
        if not self.is_open:
            self._last_grid = []

    def _compute_grid(self, screen_w: int, screen_h: int) -> tuple[int,int,int,int,int,int,int,int]:
        map_width = min(800, int(screen_w * 0.7))
        map_height = min(600, int(screen_h * 0.7))
        map_x = (screen_w - map_width) // 2
        map_y = (screen_h - map_height) // 2
        cell_size = min(map_width // 2, map_height // 2) - 20
        start_x = map_x + (map_width - cell_size * 2 - 20) // 2
        start_y = map_y + 20
        return map_x, map_y, map_width, map_height, cell_size, start_x, start_y

    def draw(self, screen_w: int, screen_h: int, current_scene: int):
        if not self.is_open:
            return

        map_x, map_y, map_width, map_height, cell_size, start_x, start_y = self._compute_grid(screen_w, screen_h)

        # Fondo
        draw_rectangle(0, 0, screen_w, screen_h, Color(0, 0, 0, 180))
        draw_rectangle(map_x - 20, map_y - 40, map_width + 40, map_height + 60, Color(50, 45, 40, 255))
        draw_rectangle_lines(map_x - 20, map_y - 40, map_width + 40, map_height + 60, Color(200, 180, 140, 255))

        # Título
        title_font = max(20, int(screen_h * 0.03))
        title_text = "MAPA DEL MUNDO"
        title_width = measure_text(title_text, title_font)
        draw_text(title_text, map_x + (map_width - title_width) // 2, map_y - 30, title_font, Color(255, 240, 200, 255))

        # Celdas 2x2
        self._last_grid = []
        for i in range(self.total_scenes):
            row = i // 2
            col = i % 2
            cell_x = start_x + col * (cell_size + 20)
            cell_y = start_y + row * (cell_size + 20)

            scene_color = self.scene_colors[i] if i < len(self.scene_colors) else GRAY
            border_color = Color(255, 220, 100, 255) if i == current_scene else Color(100, 90, 80, 255)

            draw_rectangle(cell_x, cell_y, cell_size, cell_size, scene_color)
            if i == current_scene:
                draw_rectangle_lines(cell_x - 2, cell_y - 2, cell_size + 4, cell_size + 4, border_color)
            draw_rectangle_lines(cell_x, cell_y, cell_size, cell_size, border_color)

            # Número de escena
            num_font = max(30, int(cell_size * 0.2))
            num_text = str(i + 1)
            num_w = measure_text(num_text, num_font)
            draw_text(num_text, cell_x + (cell_size - num_w) // 2, cell_y + cell_size // 2 - num_font // 2 - 20, num_font, Color(255, 255, 255, 200))

            # Nombre
            name_font = max(14, int(cell_size * 0.08))
            name = self.scene_names[i] if i < len(self.scene_names) else f"Escena {i+1}"
            name_w = measure_text(name, name_font)
            text_bg_y = cell_y + cell_size // 2 + 10
            draw_rectangle(cell_x + 10, text_bg_y - 5, cell_size - 20, name_font + 10, Color(0, 0, 0, 150))
            draw_text(name, cell_x + (cell_size - name_w) // 2, text_bg_y, name_font, Color(255, 255, 255, 255))

            # Cachea para clicks
            self._last_grid.append((i, cell_x, cell_y, cell_size, cell_size))

        # Instrucciones
        inst_font = max(12, int(screen_h * 0.018))
        inst_text = "Haz clic en una zona para viajar | [M] cerrar"
        inst_w = measure_text(inst_text, inst_font)
        draw_text(inst_text, map_x + (map_width - inst_w) // 2, map_y + map_height + 10, inst_font, Color(200, 200, 200, 255))

    def handle_click(self, screen_w: int, screen_h: int) -> int:
        """Retorna el índice de escena clickeado o -1 si ningún click válido."""
        if not self.is_open:
            return -1

        if not self._last_grid:
            # recomputa por seguridad
            self.draw(screen_w, screen_h, 0)

        mouse = get_mouse_position()
        mx, my = int(mouse.x), int(mouse.y)

        for (i, x, y, w, h) in self._last_grid:
            if mx >= x and mx <= x + w and my >= y and my <= y + h:
                return i
        return -1
