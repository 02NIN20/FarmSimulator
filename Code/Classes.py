"""Entidades del juego: GameObject, Scene, Box y Player."""

from __future__ import annotations

import math
import raylibpy as rl


class GameObject:
    """Interfaz mínima para objetos que viven dentro de una escena."""

    def update(self, dt: float) -> None:
        """Actualiza el objeto; por defecto no hace nada."""
        # Método virtual: implementar en subclases.
        return None

    def draw(self) -> None:
        """Dibuja el objeto; por defecto no hace nada."""
        # Método virtual: implementar en subclases.
        return None


class Box(GameObject):
    """Rectángulo estático de ejemplo (propio de cada escena)."""

    def __init__(self, rect: rl.Rectangle, color: rl.Color) -> None:
        self.rect = rect
        self.color = color

    def update(self, dt: float) -> None:
        """No hace nada; Box es estático."""
        return None

    def draw(self) -> None:
        """Dibuja el rectángulo y su borde."""
        rl.draw_rectangle_rec(self.rect, self.color)
        rl.draw_rectangle_lines_ex(self.rect, 2, rl.BLACK)


class Scene:
    """Contiene el estado y objetos de una escena de juego."""

    def __init__(
        self,
        scene_id: int,
        size: rl.Vector2,
        bg_color: rl.Color,
        spawn: rl.Vector2,
    ) -> None:
        self.id = scene_id
        self.size = size
        self.bg_color = bg_color
        self.spawn = spawn  # posición inicial del jugador en esta escena
        self.objects: list[GameObject] = []

    def add(self, obj: GameObject) -> GameObject:
        """Añade un objeto a la escena y lo devuelve (para encadenar)."""
        self.objects.append(obj)
        return obj

    def update(self, dt: float) -> None:
        """Actualiza todos los objetos de la escena."""
        for obj in self.objects:
            obj.update(dt)

    def center(self) -> rl.Vector2:
        """Centro geométrico de la escena (origen en 0,0)."""
        return rl.Vector2(self.size.x * 0.5, self.size.y * 0.5)

    def draw(self) -> None:
        """Dibuja el fondo, marco y objetos propios de la escena."""
        rl.draw_rectangle(0, 0, int(self.size.x), int(self.size.y), self.bg_color)
        rl.draw_rectangle_lines(0, 0, int(self.size.x), int(self.size.y), rl.BLACK)
        rl.draw_text(f"Escena {self.id}", 12, 12, 24, rl.WHITE)
        for obj in self.objects:
            obj.draw()


class Player:
    """Jugador: un cuadrado que se mueve con un tamaño y velocidad constantes."""

    def __init__(self, start_pos: rl.Vector2, size: int = 32, speed: float = 240.0, accel_time: float = 0.15) -> None:
        self.position = rl.Vector2(start_pos.x, start_pos.y)
        self.size = size
        self.speed = speed

        # Estado para el easing
        self._dir = rl.Vector2(0.0, 0.0)        # dirección de movimiento actual (unit vector)
        self._progress = 0.0                    # 0 = parado, 1 = velocidad máxima
        self.accel_time = max(0.2, accel_time)  # tiempo en segundos para alcanzar velocidad completa, modificar el primer valor para cada esceniario para simular si hay nieve o barro o algo que lo demore en acelerar

        # velocidad actual (opcional, útil para debug)
        self._velocity = rl.Vector2(0.0, 0.0)

    # --- helpers ---
    @staticmethod
    def _length(v: rl.Vector2) -> float:
        return math.hypot(v.x, v.y)

    @staticmethod
    def _normalize(v: rl.Vector2) -> rl.Vector2:
        l = Player._length(v)
        if l > 1e-9:
            return rl.Vector2(v.x / l, v.y / l)
        return rl.Vector2(0.0, 0.0)

    @staticmethod
    def _dot(a: rl.Vector2, b: rl.Vector2) -> float:
        return a.x * b.x + a.y * b.y

    @staticmethod
    def ease_in_out(t: float) -> float:
        """Smoothstep (ease in/out). t en [0,1]."""
        if t <= 0.0:
            return 0.0
        if t >= 1.0:
            return 1.0
        # smoothstep cubic Hermite
        return t * t * (3.0 - 2.0 * t)

    # --- método principal ---
    def update(self, move_axis: rl.Vector2, dt: float) -> None:
        """
        move_axis: vector de movimiento (puede venir normalizado o no).
        dt: delta time en segundos.
        """
        # decidir si hay entrada de movimiento
        mag = Player._length(move_axis)
        moving = mag > 1e-6

        if moving:
            # actualizamos dirección objetivo (normalizada)
            new_dir = Player._normalize(move_axis)

            # si la dirección cambio mucho (giro brusco), reseteamos el progreso para un nuevo ease-in
            if Player._length(self._dir) > 1e-6 and Player._dot(new_dir, self._dir) < 0.9:
                self._progress = 0.0

            self._dir = new_dir
            # incrementar progreso (aceleración)
            self._progress += dt / self.accel_time
        else:
            # no hay entrada → empezamos a desacelerar
            self._progress -= dt / self.accel_time

        # clamp
        if self._progress < 0.0:
            self._progress = 0.0
        elif self._progress > 1.0:
            self._progress = 1.0

        # aplicamos easing al progreso
        speed_mult = Player.ease_in_out(self._progress)

        # velocidad actual
        vx = self._dir.x * self.speed * speed_mult
        vy = self._dir.y * self.speed * speed_mult
        self._velocity.x = vx
        self._velocity.y = vy

        # actualización de posición usando la velocidad actual
        self.position.x += vx * dt
        self.position.y += vy * dt

    def draw(self) -> None:
        """Dibuja el jugador como un rectángulo sólido y su borde."""
        half = self.size / 2
        rect = rl.Rectangle(self.position.x - half, self.position.y - half, self.size, self.size)
        rl.draw_rectangle_rec(rect, rl.BLACK)
        rl.draw_rectangle_lines_ex(rect, 2, rl.YELLOW)
