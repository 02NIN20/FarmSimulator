import raylibpy as rl


class CameraController:
    def __init__(self, screen_center: rl.Vector2, zoom: float = 1.0):
        self.camera = rl.Camera2D()
        self.camera.offset = screen_center
        self.camera.target = rl.Vector2(0, 0)
        self.camera.rotation = 0.0
        self.camera.zoom = zoom
        self.min_zoom = 0.35
        self.max_zoom = 3.0


@property
def zoom(self) -> float:
    return self.camera.zoom


def add_zoom(self, delta: float):
    self.camera.zoom = max(self.min_zoom, min(self.max_zoom, self.camera.zoom + delta))


def follow(self, world_pos: rl.Vector2):
    self.camera.target = world_pos


def begin(self):
    rl.begin_mode_2d(self.camera)


def end(self):
    rl.end_mode_2d()