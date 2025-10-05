# asset_manager.py

from __future__ import annotations
from typing import Optional
from pyray import load_texture, unload_texture, unload_font, Font, Texture2D, get_random_value
from game_config import LOADING_IMAGE_PATH

class AssetManager:
    """Encapsula la lógica de carga y descarga de assets (texturas y fuentes)."""
    
    def __init__(self) -> None:
        self.custom_font: Optional[Font] = None
        self.loading_texture: Optional[Texture2D] = None
        self.spring_texture: Optional[Texture2D] = None
        self.loading_path = LOADING_IMAGE_PATH
        self._load_assets()

    def _load_assets(self) -> None:
        try:
            # Aquí iría la carga de fuente personalizada
            pass 
        except Exception:
            self.custom_font = None
        
        if self.loading_path is not None:
            try:
                self.loading_texture = load_texture(self.loading_path)
            except Exception:
                self.loading_texture = None

        try:
            self.spring_texture = load_texture("assets/apertura.png")
        except Exception:
            self.spring_texture = None

    def unload_assets(self) -> None:
        if self.custom_font is not None:
            unload_font(self.custom_font)
            self.custom_font = None
        if self.loading_texture is not None:
            unload_texture(self.loading_texture)
            self.loading_texture = None
        if self.spring_texture is not None:
            unload_texture(self.spring_texture)
            self.spring_texture = None