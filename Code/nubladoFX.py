from pyray import *
import random 
import math 
import sys 

class NubladoFX:
    """Gestiona la simulación visual y el estado de las sombras de nubes con viento."""

    SCALE = 10              
    MAX_CLOUD_COUNT = 500   
    MARGIN_GEN = 150        

    def __init__(self, screen_w: int, screen_h: int) -> None:
        self.width = screen_w
        self.height = screen_h
        self.clouds = []
        self.wind_angle = 0.0 
        self.wind_speed = 0.0 

    def _create_cloud(self, x: float, y: float) -> dict:
        """Método privado que crea una nube con forma orgánica."""
        cloud = {"x": x, "y": y, "circles": [], "alpha": 0.0, "target_alpha": 1.0}
        # ... (resto del código de creación de círculos)
        num_parts = random.randint(3, 10) 
        base_radius = random.randint(50, 150)
        base_shadow_alpha = random.randint(60, 90) 

        for i in range(num_parts):
            offset_r = random.uniform(base_radius * 0.1, base_radius * 1.5)
            offset_a = random.uniform(0, 2 * math.pi)
            offset_x = offset_r * math.cos(offset_a)
            offset_y = offset_r * math.sin(offset_a)
            radius = random.uniform(base_radius * 0.2, base_radius * 0.8)
            cloud["circles"].append({
                "offset_x": offset_x,
                "offset_y": offset_y,
                "radius": radius,
                "base_alpha": base_shadow_alpha 
            })
        return cloud


    def _is_off_screen(self, c: dict) -> bool:
        # ... (código existente)
        margin = max(c["circles"], key=lambda p: p["radius"])["radius"] if c["circles"] else 150
        return (c["x"] < -margin or 
                c["x"] > self.width + margin or
                c["y"] < -margin or 
                c["y"] > self.height + margin)

    def update(self, frame_time: float, cloudiness: float, wind_speed_m_s: float, wind_angle_rad: float):
        # ... (código existente de update: movimiento y generación)
        self.wind_speed = wind_speed_m_s
        self.wind_angle = wind_angle_rad

        wind_px_sec = self.wind_speed * self.SCALE 
        dx = wind_px_sec * math.cos(self.wind_angle) * frame_time
        dy = wind_px_sec * math.sin(self.wind_angle) * frame_time

        temp_clouds = []
        for c in self.clouds:
            c["x"] += dx
            c["y"] += dy
            
            if c["target_alpha"] > c["alpha"]:
                c["alpha"] = min(c["target_alpha"], c["alpha"] + frame_time * 1.5)
            elif c["target_alpha"] < c["alpha"]:
                c["alpha"] = max(0.0, c["alpha"] - frame_time * 1.5)

            if not self._is_off_screen(c) or c["alpha"] > sys.float_info.epsilon:
                temp_clouds.append(c)
                
        self.clouds = temp_clouds

        if cloudiness > 0.0 and len(self.clouds) < self.MAX_CLOUD_COUNT:
            gen_rate = max(0.1, cloudiness) * 1.0 
            
            if random.random() < gen_rate * frame_time * 10:
                is_entering_horizontally = abs(math.cos(self.wind_angle)) > abs(math.sin(self.wind_angle))
                
                if is_entering_horizontally:
                    if math.cos(self.wind_angle) < 0: 
                        x, y = self.width + self.MARGIN_GEN, random.uniform(0, self.height)
                    else: 
                        x, y = -self.MARGIN_GEN, random.uniform(0, self.height)
                else:
                    if math.sin(self.wind_angle) < 0: 
                        x, y = random.uniform(0, self.width), self.height + self.MARGIN_GEN
                    else: 
                        x, y = random.uniform(0, self.width), -self.MARGIN_GEN

                new_cloud = self._create_cloud(x, y)
                new_cloud["alpha"] = 0.0 
                self.clouds.append(new_cloud)

    def draw(self):
        """Dibuja las sombras de las nubes como un overlay en pantalla."""
        
        # Importante: No hay begin_drawing() ni end_drawing() aquí.
        for c in self.clouds:
            if c["alpha"] > sys.float_info.epsilon:
                for part in c["circles"]:
                    final_alpha = int(part["base_alpha"] * c["alpha"])
                    final_alpha = max(0, min(255, final_alpha)) 
                    
                    draw_circle(
                        int(c["x"] + part["offset_x"]),
                        int(c["y"] + part["offset_y"]),
                        part["radius"],
                        Color(120, 120, 120, final_alpha) # Color gris para la sombra
                    )