# collisions.py
from typing import List

class CollisionMap:
    def __init__(self, cols: int, rows: int):
        self.cols = cols
        self.rows = rows
        self.grid: List[bool] = [False] * (cols * rows)

    def _idx(self, c: int, r: int) -> int:
        if c < 0 or r < 0 or c >= self.cols or r >= self.rows:
            return -1
        return r * self.cols + c

    def set_solid(self, c: int, r: int, solid: bool = True):
        i = self._idx(c, r)
        if i >= 0:
            self.grid[i] = solid

    def is_solid(self, c: int, r: int) -> bool:
        i = self._idx(c, r)
        return False if i < 0 else self.grid[i]

    def rect_collides(self, x: float, y: float, w: float, h: float, cell_w: int, cell_h: int) -> bool:
        left = int(x // cell_w)
        right = int((x + w) // cell_w)
        top = int(y // cell_h)
        bottom = int((y + h) // cell_h)

        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if self.is_solid(c, r):
                    return True
        return False
