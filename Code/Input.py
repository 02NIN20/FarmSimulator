import raylibpy as rl


# Devuelve vector de movimiento en ejes X/Y según WASD o flechas

def get_move_axis() -> rl.Vector2:
    x = 0
    y = 0
    
    if rl.is_key_down(rl.KEY_A) or rl.is_key_down(rl.KEY_LEFT):
        x -= 1
    if rl.is_key_down(rl.KEY_D) or rl.is_key_down(rl.KEY_RIGHT):
        x += 1
    if rl.is_key_down(rl.KEY_W) or rl.is_key_down(rl.KEY_UP):
        y -= 1
    if rl.is_key_down(rl.KEY_S) or rl.is_key_down(rl.KEY_DOWN):
        y += 1


    if x != 0 or y != 0:
        v = rl.Vector2(float(x), float(y))
        length = (v.x * v.x + v.y * v.y) ** 0.5
        v.x /= length
        v.y /= length
        return v
    return rl.Vector2(0.0, 0.0)