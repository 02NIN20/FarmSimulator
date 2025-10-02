# map_system.py

from __future__ import annotations
from typing import List
from pyray import *

class MapSystem:
    """Sistema de mapa del mundo."""
    def __init__(self, total_scenes: int):
        self.is_open: bool = False
        self.total_scenes = total_scenes
        
        # Colores para cada escena (deben coincidir con los de las escenas)
        self.scene_colors = [
            Color(70, 120, 200, 255),   # Escena 1
            Color(200, 120, 70, 255),   # Escena 2
            Color(80, 160, 110, 255),   # Escena 3
            Color(160, 80, 160, 255),   # Escena 4
        ]
        
        # Nombres de las escenas
        self.scene_names = [
            "Zona Norte - Pradera",
            "Zona Este - Desierto",
            "Zona Sur - Bosque",
            "Zona Oeste - Montaña"
        ]
    
    def toggle(self):
        """Abre o cierra el mapa."""
        self.is_open = not self.is_open
    
    def draw(self, screen_w: int, screen_h: int, current_scene: int):
        """Dibuja la interfaz del mapa."""
        if not self.is_open:
            return
        
        # Fondo semi-transparente
        draw_rectangle(0, 0, screen_w, screen_h, Color(0, 0, 0, 180))
        
        # Panel del mapa
        map_width = min(800, int(screen_w * 0.7))
        map_height = min(600, int(screen_h * 0.7))
        
        map_x = (screen_w - map_width) // 2
        map_y = (screen_h - map_height) // 2
        
        # Panel principal
        draw_rectangle(map_x - 20, map_y - 40, map_width + 40, map_height + 60, Color(50, 45, 40, 255))
        draw_rectangle_lines(map_x - 20, map_y - 40, map_width + 40, map_height + 60, Color(200, 180, 140, 255))
        
        # Título
        title_font = max(20, int(screen_h * 0.03))
        title_text = "MAPA DEL MUNDO"
        title_width = measure_text(title_text, title_font)
        draw_text(title_text, map_x + (map_width - title_width) // 2, map_y - 30, title_font, Color(255, 240, 200, 255))
        
        # Dibujar grid de escenas (2x2)
        cell_size = min(map_width // 2, map_height // 2) - 20
        start_x = map_x + (map_width - cell_size * 2 - 20) // 2
        start_y = map_y + 20
        
        for i in range(self.total_scenes):
            row = i // 2
            col = i % 2
            
            cell_x = start_x + col * (cell_size + 20)
            cell_y = start_y + row * (cell_size + 20)
            
            # Color de la escena
            scene_color = self.scene_colors[i] if i < len(self.scene_colors) else GRAY
            
            # Resaltar escena actual
            border_color = Color(255, 220, 100, 255) if i == current_scene else Color(100, 90, 80, 255)
            border_width = 4 if i == current_scene else 2
            
            # Dibujar celda
            draw_rectangle(cell_x, cell_y, cell_size, cell_size, scene_color)
            
            # Dibujar borde múltiple para escena actual
            if i == current_scene:
                draw_rectangle_lines(cell_x - 2, cell_y - 2, cell_size + 4, cell_size + 4, border_color)
            draw_rectangle_lines(cell_x, cell_y, cell_size, cell_size, border_color)
            
            # Número de escena
            num_font = max(30, int(cell_size * 0.2))
            num_text = str(i + 1)
            num_w = measure_text(num_text, num_font)
            draw_text(num_text, cell_x + (cell_size - num_w) // 2, 
                     cell_y + cell_size // 2 - num_font // 2 - 20, num_font, Color(255, 255, 255, 200))
            
            # Nombre de la escena
            name_font = max(14, int(cell_size * 0.08))
            name = self.scene_names[i] if i < len(self.scene_names) else f"Zona {i+1}"
            name_w = measure_text(name, name_font)
            
            # Fondo para el texto
            text_bg_y = cell_y + cell_size // 2 + 10
            draw_rectangle(cell_x + 10, text_bg_y - 5, cell_size - 20, name_font + 10, Color(0, 0, 0, 150))
            draw_text(name, cell_x + (cell_size - name_w) // 2, text_bg_y, name_font, Color(255, 255, 255, 255))
            
            # Indicador de ubicación actual
            if i == current_scene:
                indicator_size = max(12, int(cell_size * 0.08))
                draw_circle(cell_x + cell_size // 2, cell_y + 30, indicator_size, Color(255, 220, 100, 255))
                draw_circle(cell_x + cell_size // 2, cell_y + 30, indicator_size - 3, Color(255, 100, 100, 255))
                
                loc_font = max(10, int(cell_size * 0.06))
                loc_text = "Estas aqui"
                loc_w = measure_text(loc_text, loc_font)
                draw_text(loc_text, cell_x + (cell_size - loc_w) // 2, 
                         cell_y + 45, loc_font, Color(255, 255, 255, 255))
        
        # Leyenda
        legend_y = map_y + map_height - 40
        legend_font = max(12, int(screen_h * 0.018))
        draw_text("Presiona teclas [1-4] para cambiar de zona", map_x + 10, legend_y, legend_font, Color(220, 220, 220, 255))
        
        # Instrucciones
        inst_font = max(12, int(screen_h * 0.018))
        inst_text = "Presiona [M] para cerrar el mapa"
        inst_width = measure_text(inst_text, inst_font)
        draw_text(inst_text, map_x + (map_width - inst_width) // 2, 
                 map_y + map_height + 10, inst_font, Color(200, 200, 200, 255))