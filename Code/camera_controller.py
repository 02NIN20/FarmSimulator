"""Control de cámara 2D para raylib-py.

La tarea que ejecuta este apartado es exponer `CameraController`, un pequeño wrapper de `rl.Camera2D` que:
- gestiona límites de zoom,
- sigue una posición en el mundo,
- facilita begin()/end() del modo 2D con nombres compatibles.
"""

from __future__ import annotations

import raylibpy as rl

# Wrappers tolerantes a nombres (algunas bindings usan begin_mode2d / end_mode2d)
_BEGIN_MODE_2D = getattr(rl, "begin_mode_2d", getattr(rl, "begin_mode2d", None))
_END_MODE_2D = getattr(rl, "end_mode_2d", getattr(rl, "end_mode2d", None))


class CameraController:
    """Pequeño controlador para `rl.Camera2D`.

    Args:
        screen_center: Offset de la cámara (centro de la pantalla).
        zoom: Zoom inicial.
        min_zoom: Límite inferior de zoom.
        max_zoom: Límite superior de zoom.
    """

    def __init__(
        self,
        screen_center: rl.Vector2,
        zoom: float = 1.0,
        min_zoom: float = 0.35,
        max_zoom: float = 3.0,
    ) -> None:
        self.camera = rl.Camera2D()
        self.camera.offset = screen_center
        self.camera.target = rl.Vector2(0.0, 0.0)
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

    def follow(self, world_pos: rl.Vector2) -> None:
        """Hace que la cámara siga la posición `world_pos` (coordenadas de mundo)."""
        self.camera.target = world_pos

    def begin(self) -> None:
        """Activa el modo 2D usando la cámara interna."""
        if _BEGIN_MODE_2D is None:
            raise AttributeError("raylibpy: no se encontró begin_mode_2d/begin_mode2d")
        _BEGIN_MODE_2D(self.camera)

    def end(self) -> None:
        """Finaliza el modo 2D."""
        if _END_MODE_2D is None:
            raise AttributeError("raylibpy: no se encontró end_mode_2d/end_mode2d")
        _END_MODE_2D()
