# world_manager.py

from __future__ import annotations
from typing import List, Dict
from pyray import Vector2, Color, Rectangle
from scene import Scene # Asumimos que Scene está definido en scene.py
# Importa la geometría estática de las zonas
from zones_geometry import zone2_alaska_polygon, zone3_ppr_polygon, zone4_michigan_polygon

class WorldManager:
    """Encapsula la creación de escenas, las coordenadas de spawn y la geometría estática."""
    
    def __init__(self, scene_w: int, scene_h: int) -> None:
        self.scene_w = scene_w
        self.scene_h = scene_h
        
        # Geometría estática
        self.cabins: dict[int, list[Rectangle]] = {}
        self.workbenches: dict[int, list[Rectangle]] = {}
        self.furnaces_pos: dict[int, list[Rectangle]] = {}

        self.scenes = self._create_scenes()
        self._setup_cabins() 
        self._setup_crafting_stations()

    def _make_scene(self, scene_id: int, land: Color) -> Scene:
        size = Vector2(self.scene_w, self.scene_h)
        spawn = Vector2(self.scene_w * 0.5, self.scene_h * 0.5)
        return Scene(scene_id, size, land, spawn, land_color=land)
    
    def scene_center(self, scene: Scene) -> Vector2:
        return Vector2(scene.size.x * 0.5, scene.size.y * 0.5)

    def _create_scenes(self) -> List[Scene]:
        LOCAL_LAND   = Color(128, 178, 112, 255)
        ALASKA_LAND  = Color(100, 142, 120, 255)
        PPR_LAND     = Color(160, 175,  90, 255)
        MICH_LAND    = Color( 92, 150, 110, 255)

        s1 = self._make_scene(1, LOCAL_LAND)
        s2 = Scene(2, Vector2(self.scene_w, self.scene_h), ALASKA_LAND,
                   Vector2(self.scene_w*0.5, self.scene_h*0.5),
                   grid_cell_size=48, grid_enabled=True,
                   polygon_norm=zone2_alaska_polygon(), land_color=ALASKA_LAND)
        s3 = Scene(3, Vector2(self.scene_w, self.scene_h), PPR_LAND,
                   Vector2(self.scene_w*0.5, self.scene_h*0.5),
                   grid_cell_size=48, grid_enabled=True,
                   polygon_norm=zone3_ppr_polygon(), land_color=PPR_LAND)
        s4 = Scene(4, Vector2(self.scene_w, self.scene_h), MICH_LAND,
                   Vector2(self.scene_w*0.5, self.scene_h*0.5),
                   grid_cell_size=48, grid_enabled=True,
                   polygon_norm=zone4_michigan_polygon(), land_color=MICH_LAND)
        return [s1, s2, s3, s4]

    def _setup_cabins(self) -> None:
        # Lógica original para inicializar self.cabins
        pass 
    
    def _setup_crafting_stations(self) -> None:
        # Lógica original para inicializar workbenches y furnaces
        pass