# game_clock.py

from typing import List, ClassVar

class GameClock:
    SEASONS: ClassVar[List[str]] = ["Primavera", "Verano", "Otoño", "Invierno"]
    
    def __init__(self, seconds_per_day: float = 300.0) -> None:
        self.seconds_per_day = max(1.0, seconds_per_day)
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    @property
    def day_fraction(self) -> float:
        return (self.elapsed % self.seconds_per_day) / self.seconds_per_day

    @property
    def day(self) -> int:
        return int(self.elapsed // self.seconds_per_day) + 1

    def time_hhmm(self) -> str:
        total_minutes = int(self.day_fraction * 24 * 60)
        hh = total_minutes // 60
        mm = total_minutes % 60
        return f"{hh:02d}:{mm:02d}"

    def season_name(self) -> str:
        season_len = 30
        idx = ((self.day - 1) // season_len) % len(self.SEASONS)
        return self.SEASONS[idx]