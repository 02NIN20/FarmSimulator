"""Control de cámara 2D para paylib.

La tarea que ejecuta este apartado es exponer `CameraController`, un pequeño wrapper de `Camera2D` que:
- gestiona límites de zoom,
- sigue una posición en el mundo,
- facilita begin()/end() del modo 2D con nombres compatibles.
"""

from __future__ import annotations

from paylib import *

class CameraController:
    """Pequeño controlador para `Camera2D`.

    Args:
        screen_center: Offset de la cámara (centro de la pantalla).
        zoom: Zoom inicial.
        min_zoom: Límite inferior de zoom.
        max_zoom: Límite superior de zoom.
    """

    def __init__(
        self,
        screen_center: Vector2,
        zoom: float = 1.0,
        min_zoom: float = 0.35,
        max_zoom: float = 3.0,
    ) -> None:
        self.camera = Camera2D()
        self.camera.offset = screen_center
        self.camera.target = Vector2(0.0, 0.0)
        self.camera.rotation = 0.0
        self.camera.zoom = zoom
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom

    @property
    def zoom(self) -> float:
        """Devuelve el zoom actual de la cámara."""
        return self.camera.zoom

    def add_zoom(self, delta: float) -> None:
        """Modifica el zoom y lo limita a [min_zoom, max_zoom]."""
        self.camera.zoom = max(
            self.min_zoom, min(self.max_zoom, self.camera.zoom + delta)
        )

    def follow(self, world_pos: Vector2) -> None:
        """Hace que la cámara siga la posición `world_pos` (coordenadas de mundo)."""
        self.camera.target = world_pos

    def begin(self) -> None:
        """Activa el modo 2D usando la cámara interna."""
        begin_mode2d(self.camera)

    def end(self) -> None:
        """Finaliza el modo 2D."""
        end_mode2d()