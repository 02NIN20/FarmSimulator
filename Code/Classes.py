import raylibpy as rl

class GameObject:
    """Interfaz mínima para objetos que viven dentro de una escena."""
    def update(self, dt: float):
        pass

    def draw(self):
        pass


class Box(GameObject):
    """Rectángulo estático de ejemplo (propio de cada escena)."""
    def __init__(self, rect: rl.Rectangle, color: rl.Color):
        self.rect = rect
        self.color = color

    def update(self, dt: float):
        pass

    def draw(self):
        rl.draw_rectangle_rec(self.rect, self.color)
        rl.draw_rectangle_lines_ex(self.rect, 2, rl.BLACK)


class Scene:
    def __init__(self, scene_id: int, size: rl.Vector2, bg_color: rl.Color, spawn: rl.Vector2):
        self.id = scene_id
        self.size = size
        self.bg_color = bg_color
        self.spawn = spawn              # posición inicial del jugador en esta escena
        self.objects: list[GameObject] = []

    def add(self, obj: GameObject):
        self.objects.append(obj)
        return obj

    def update(self, dt: float):
        for o in self.objects:
            o.update(dt)

    def center(self) -> rl.Vector2:
        """Centro geométrico de la escena (origen en 0,0)."""
        return rl.Vector2(self.size.x * 0.5, self.size.y * 0.5)
    
    def draw(self):
        # Fondo de la escena (tamaño completo)
        rl.draw_rectangle(0, 0, int(self.size.x), int(self.size.y), self.bg_color)
        rl.draw_rectangle_lines(0, 0, int(self.size.x), int(self.size.y), rl.BLACK)
        rl.draw_text(f"Escena {self.id}", 12, 12, 24, rl.WHITE)
        # Objetos propios de esta escena
        for o in self.objects:
            o.draw()


class Player:
    def __init__(self, start_pos: rl.Vector2, size: int = 32, speed: float = 240.0):
        self.position = rl.Vector2(start_pos.x, start_pos.y)
        self.size = size
        self.speed = speed

    def update(self, move_axis: rl.Vector2, dt: float):
        self.position.x += move_axis.x * self.speed * dt
        self.position.y += move_axis.y * self.speed * dt

    def draw(self):
        half = self.size / 2
        rect = rl.Rectangle(self.position.x - half, self.position.y - half, self.size, self.size)
        rl.draw_rectangle_rec(rect, rl.BLACK)
        rl.draw_rectangle_lines_ex(rect, 2, rl.YELLOW)
