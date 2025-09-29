# main.py

from __future__ import annotations
from game import Game, RESOLUTIONS

def main() -> None:
    # Obtener el índice de la resolución inicial (la más pequeña, como estaba en el código original)
    initial_res_index = len(RESOLUTIONS) - 1
    
    # Inicializar y ejecutar el juego
    game = Game(initial_res_index)
    game.run()

if __name__ == "__main__":
    main()