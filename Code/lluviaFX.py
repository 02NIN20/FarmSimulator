from pyray import *
import random
import math

class LluviaFX:
    """Gestiona la simulación visual y el estado de los impactos de lluvia."""

    IMPACT_LIFETIME = 0.5    
    IMPACT_SIZE_MAX = 10.0   
    IMPACT_GENERATION_BASE = 500 

    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.width = screen_w
        self.height = screen_h
        self.splashes = []
    
    def _create_impact(self, x: float, y: float) -> dict:
        """Método privado que crea una onda de impacto en el piso."""
        max_radius = self.IMPACT_SIZE_MAX * random.uniform(0.7, 1)
        
        return {
            "x": x,
            "y": y,
            "lifetime": self.IMPACT_LIFETIME,
            "max_lifetime": self.IMPACT_LIFETIME,
            "max_radius": max_radius
        }

    def update(self, frame_time: float, intensity: float):
        """Actualiza el estado de la lluvia."""
        
        impact_rate = self.IMPACT_GENERATION_BASE * intensity
        impacts_to_generate_float = impact_rate * frame_time
        impacts_to_generate = int(impacts_to_generate_float)
        remainder_probability = impacts_to_generate_float - impacts_to_generate

        for _ in range(impacts_to_generate):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            self.splashes.append(self._create_impact(x, y))

        if random.random() < remainder_probability:
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            self.splashes.append(self._create_impact(x, y))

        temp_splashes = []
        for splash in self.splashes:
            splash["lifetime"] -= frame_time
            if splash["lifetime"] > 0:
                temp_splashes.append(splash)
                
        self.splashes = temp_splashes

    def draw(self):
        """Dibuja las ondas de impacto de la lluvia como un overlay en pantalla."""
        
        # Importante: No hay begin_drawing() ni end_drawing() aquí.
        for splash in self.splashes:
            life_progress = 1.0 - (splash["lifetime"] / splash["max_lifetime"])
            current_radius = splash["max_radius"] * life_progress
            current_alpha = int(255 * (1.0 - (life_progress * 0.8))) 

            draw_ring_lines(
                Vector2(splash["x"], splash["y"]),
                current_radius - 1, 
                current_radius,     
                0, 360, 30, 
                Color(173, 216, 230, current_alpha) 
            )