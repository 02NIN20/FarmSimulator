# main.py

from __future__ import annotations
from game import Game, RESOLUTIONS

def main():
    # coge 960x540 por defecto
    res_index = 5
    game = Game(res_index)
    game.run()

if __name__ == "__main__":
    main()
