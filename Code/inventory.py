# inventory.py

from __future__ import annotations
from typing import Dict, Optional, Tuple, List
from pyray import *

# ============ Modelo de datos ============

class Item:
    """Representa un item en el inventario."""
    def __init__(
        self,
        item_id: str,
        name: str,
        description: str,
        icon_color: Color,
        stackable: bool = True,
        max_stack: int = 99,
    ):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.icon_color = icon_color
        self.stackable = stackable
        self.max_stack = max_stack


class InventorySlot:
    def __init__(self) -> None:
        self.item: Optional[Item] = None
        self.quantity: int = 0

    def is_empty(self) -> bool:
        return self.item is None or self.quantity <= 0

    def clear(self) -> None:
        self.item = None
        self.quantity = 0

    def can_stack_with(self, other: Item) -> bool:
        return (
            self.item is not None
            and self.item.stackable
            and other.stackable
            and self.item.item_id == other.item_id
            and self.quantity < self.item.max_stack
        )

    def add_item(self, item: Item, amount: int) -> int:
        """Añade al slot y devuelve la cantidad que NO cupo (restante)."""
        if amount <= 0:
            return 0

        if self.is_empty():
            self.item = item
            if item.stackable:
                cap = item.max_stack
                add = min(cap, amount)
                self.quantity = add
                return amount - add
            else:
                self.quantity = 1
                return amount - 1

        # Slot ocupado
        if not self.item.stackable:
            # No se puede apilar en herramientas
            return amount

        if self.item.item_id != item.item_id:
            # No coincide el tipo
            return amount

        cap = self.item.max_stack
        free = cap - self.quantity
        if free <= 0:
            return amount
        add = min(free, amount)
        self.quantity += add
        return amount - add


# ============ Inventario ============

class Inventory:
    def __init__(self, rows: int = 4, cols: int = 10) -> None:
        self.rows = max(1, rows)
        self.cols = max(1, cols)
        self.slots: List[InventorySlot] = [InventorySlot() for _ in range(self.rows * self.cols)]
        self.is_open = False

        # Para arrastrar/soltar
        self.dragging_item: Optional[Item] = None
        self.dragging_qty: int = 0
        self.drag_origin_index: Optional[int] = None

        # Base mínima para que el juego arranque con lo que ya usabas
        self.item_database: Dict[str, Item] = {
            "seed_corn": Item("seed_corn", "Semilla de Maíz", "Semilla para cultivar maíz", Color(240, 210, 100, 255)),
            "seed_wheat": Item("seed_wheat", "Semilla de Trigo", "Semilla para cultivar trigo", Color(235, 215, 150, 255)),
            "water": Item("water", "Agua", "Recurso básico", Color(120, 190, 255, 255), True, 99),
            "fertilizer": Item("fertilizer", "Fertilizante", "Aporta nutrientes", Color(150, 160, 90, 255), True, 99),
        }

        # Catálogo extendido (items_registry.py)
        try:
            from items_registry import iter_all_items  # type: ignore
            for item_id, name, description, color, stackable, max_stack in iter_all_items():
                if item_id not in self.item_database:
                    self.item_database[item_id] = Item(
                        item_id, name, description, color,
                        stackable=stackable, max_stack=max_stack
                    )
        except Exception as e:
            print("[inventory] No se pudo cargar items_registry:", e)

    # ----- API -----

    def toggle(self) -> None:
        self.is_open = not self.is_open
        # cancelar drag si se cierra
        if not self.is_open:
            self._cancel_drag()

    def add_item(self, item_id: str, amount: int = 1) -> bool:
        """Intentar añadir 'amount' del item. Devuelve True si todo cupo."""
        if amount <= 0:
            return True
        item = self.item_database.get(item_id)
        if item is None:
            print(f"[inventory] Item desconocido: {item_id}")
            return False

        remaining = amount

        # Primero llenar slots existentes con el mismo item (apilable)
        if item.stackable:
            for slot in self.slots:
                if slot.can_stack_with(item):
                    remaining = slot.add_item(item, remaining)
                    if remaining <= 0:
                        return True

        # Luego buscar slots vacíos
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add_item(item, remaining)
                if remaining <= 0:
                    return True

        return False  # No cupo todo

    def remove_item(self, item_id: str, amount: int = 1) -> int:
        """Elimina hasta 'amount' unidades, retorna cuántas se eliminaron."""
        removed = 0
        for slot in self.slots:
            if slot.is_empty():
                continue
            if slot.item.item_id != item_id:
                continue
            take = min(slot.quantity, amount - removed)
            slot.quantity -= take
            removed += take
            if slot.quantity <= 0:
                slot.clear()
            if removed >= amount:
                break
        return removed

    # ----- Dibujo e interacción -----

    def draw(self, screen_w: int, screen_h: int) -> None:
        if not self.is_open:
            return

        # Fondo translúcido
        draw_rectangle(0, 0, screen_w, screen_h, Color(0, 0, 0, 140))

        # Layout base
        inv_width = int(screen_w * 0.80)
        inv_height = int(screen_h * 0.62)
        inv_x = (screen_w - inv_width) // 2
        inv_y = int(screen_h * 0.16)

        # Panel
        self._draw_panel(inv_x, inv_y, inv_width, inv_height, Color(45, 38, 32, 240), Color(15, 10, 8, 255))

        # Título
        title = "INVENTARIO"
        title_fs = max(20, int(screen_h * 0.035))
        draw_text(title, inv_x + 20, inv_y + 16, title_fs, Color(235, 220, 180, 255))

        # Rejilla
        grid_x = inv_x + 20
        grid_y = inv_y + int(20 + title_fs + 12)
        grid_w = inv_width - 40
        grid_h = inv_height - (grid_y - inv_y) - 20

        slot_gap = max(6, int(min(screen_w, screen_h) * 0.007))
        # Calculamos tamaño de slot homogéneo:
        slot_w = (grid_w - (self.cols - 1) * slot_gap) // self.cols
        slot_h = (grid_h - (self.rows - 1) * slot_gap) // self.rows
        slot_size = min(slot_w, slot_h)
        # Re-centra si sobra espacio
        grid_real_w = self.cols * slot_size + (self.cols - 1) * slot_gap
        grid_real_h = self.rows * slot_size + (self.rows - 1) * slot_gap
        grid_x = grid_x + (grid_w - grid_real_w) // 2
        grid_y = grid_y + (grid_h - grid_real_h) // 2

        mouse = get_mouse_position()
        mx, my = int(mouse.x), int(mouse.y)

        hovered_index = self._slot_index_at(mx, my, grid_x, grid_y, slot_size, slot_gap)

        # Interacción de arrastrar/soltar
        if is_mouse_button_pressed(MOUSE_LEFT_BUTTON):
            self._on_mouse_press(hovered_index)

        if is_mouse_button_released(MOUSE_LEFT_BUTTON):
            self._on_mouse_release(hovered_index)

        # Dibujar slots
        font_qty = max(14, int(slot_size * 0.26))
        for r in range(self.rows):
            for c in range(self.cols):
                i = r * self.cols + c
                sx = grid_x + c * (slot_size + slot_gap)
                sy = grid_y + r * (slot_size + slot_gap)
                self._draw_slot(sx, sy, slot_size, self.slots[i], i == hovered_index)

        # Tooltip si corresponde (y no estamos arrastrando)
        if hovered_index is not None and self.dragging_item is None:
            slot = self.slots[hovered_index]
            if not slot.is_empty():
                self._draw_tooltip(screen_w, screen_h, mx, my, slot.item, slot.quantity)

        # Si estamos arrastrando, dibujar el item “fantasma” junto al cursor
        if self.dragging_item is not None and self.dragging_qty > 0:
            ghost = int(slot_size * 0.72)
            gx = mx - ghost // 2
            gy = my - ghost // 2
            draw_rectangle(gx, gy, ghost, ghost, self.dragging_item.icon_color)
            draw_rectangle_lines(gx, gy, ghost, ghost, Color(0, 0, 0, 170))
            if self.dragging_item.stackable and self.dragging_qty > 1:
                txt = str(self.dragging_qty)
                tf = max(12, int(ghost * 0.30))
                draw_text(txt, gx + ghost - measure_text(txt, tf) - 4, gy + ghost - tf - 3, tf, WHITE)

        # Instrucciones
        inst_fs = max(12, int(screen_h * 0.018))
        inst_text = "Arrastra para mover | Click para tomar/dejar | [I] cerrar"
        inst_w = measure_text(inst_text, inst_fs)
        draw_text(inst_text, inv_x + (inv_width - inst_w) // 2, inv_y + inv_height - inst_fs - 10, inst_fs, Color(200, 200, 200, 255))

    # ----- Helpers UI -----

    def _draw_panel(self, x: int, y: int, w: int, h: int, fill: Color, border: Color) -> None:
        draw_rectangle(x + 3, y + 3, w, h, Color(0, 0, 0, 80))
        try:
            draw_rectangle_rounded(Rectangle(x, y, w, h), 0.06, 8, fill)
            draw_rectangle_rounded_lines(Rectangle(x, y, w, h), 0.06, 8, 2, border)
        except Exception:
            draw_rectangle(x, y, w, h, fill)
            draw_rectangle_lines(x, y, w, h, border)

    def _draw_slot(self, x: int, y: int, size: int, slot: InventorySlot, hovered: bool) -> None:
        # Marco del slot
        draw_rectangle(x, y, size, size, Color(60, 55, 50, 220))
        draw_rectangle_lines(x, y, size, size, Color(20, 15, 10, 220))
        if hovered:
            draw_rectangle_lines(x - 2, y - 2, size + 4, size + 4, Color(255, 220, 120, 255))

        # Contenido
        if not slot.is_empty():
            icon = int(size * 0.72)
            ix = x + (size - icon) // 2
            iy = y + (size - icon) // 2
            draw_rectangle(ix, iy, icon, icon, slot.item.icon_color)
            draw_rectangle_lines(ix, iy, icon, icon, Color(0, 0, 0, 160))

            if slot.item.stackable and slot.quantity > 1:
                qtxt = str(slot.quantity)
                qf = max(12, int(size * 0.26))
                draw_text(qtxt, x + size - measure_text(qtxt, qf) - 5, y + size - qf - 4, qf, WHITE)

    def _draw_tooltip(self, screen_w: int, screen_h: int, mx: int, my: int, item: Item, qty: int) -> None:
        title_fs = max(14, int(screen_h * 0.022))
        text_fs = max(12, int(screen_h * 0.018))

        title_w = measure_text(item.name, title_fs)
        desc_w = measure_text(item.description, text_fs)
        tooltip_w = max(180, title_w + 20, desc_w + 20)
        tooltip_h = int(text_fs * 2.2) + title_fs + 16

        tx = min(mx + 16, screen_w - tooltip_w - 8)
        ty = min(my + 16, screen_h - tooltip_h - 8)

        draw_rectangle(tx, ty, tooltip_w, tooltip_h, Color(40, 35, 30, 240))
        draw_rectangle_lines(tx, ty, tooltip_w, tooltip_h, Color(200, 180, 140, 255))
        draw_text(item.name, tx + 10, ty + 6, title_fs, Color(255, 230, 150, 255))
        draw_text(item.description, tx + 10, ty + 8 + title_fs, text_fs, Color(220, 220, 220, 255))

    # ----- Drag & Drop interno -----

    def _slot_index_at(self, mx: int, my: int, gx: int, gy: int, size: int, gap: int) -> Optional[int]:
        # Determina en qué celda cae el mouse
        for r in range(self.rows):
            for c in range(self.cols):
                sx = gx + c * (size + gap)
                sy = gy + r * (size + gap)
                if gx <= mx < gx + self.cols * (size + gap) - gap and gy <= my < gy + self.rows * (size + gap) - gap:
                    if sx <= mx < sx + size and sy <= my < sy + size:
                        return r * self.cols + c
        return None

    def _on_mouse_press(self, index: Optional[int]) -> None:
        if index is None:
            return
        slot = self.slots[index]
        if self.dragging_item is None:
            # Tomar del slot
            if slot.is_empty():
                return
            self.dragging_item = slot.item
            self.dragging_qty = slot.quantity
            self.drag_origin_index = index
            slot.clear()
        else:
            # Ya hay algo en mano -> intentar dejar/combinar
            self._drop_on_index(index)

    def _on_mouse_release(self, index: Optional[int]) -> None:
        if self.dragging_item is None:
            return
        # Soltar sobre un slot válido
        if index is not None:
            self._drop_on_index(index)
        # Si aún seguimos cargando el item, intentar volver al origen
        if self.dragging_item is not None and self.drag_origin_index is not None:
            origin = self.slots[self.drag_origin_index]
            # Si origen está vacío, vuelve allí
            if origin.is_empty():
                origin.item = self.dragging_item
                origin.quantity = self.dragging_qty
                self._cancel_drag()

    def _drop_on_index(self, index: int) -> None:
        if self.dragging_item is None or self.dragging_qty <= 0:
            return
        slot = self.slots[index]

        if slot.is_empty():
            # Dejar todo aquí
            slot.item = self.dragging_item
            slot.quantity = self.dragging_qty
            self._cancel_drag()
            return

        # Si es apilable y del mismo tipo -> merge hasta el máximo
        if slot.item and slot.item.item_id == self.dragging_item.item_id and slot.item.stackable:
            cap = slot.item.max_stack
            free = max(0, cap - slot.quantity)
            if free > 0:
                moved = min(free, self.dragging_qty)
                slot.quantity += moved
                self.dragging_qty -= moved
                if self.dragging_qty <= 0:
                    self._cancel_drag()
                    return
            # si sobró, seguimos con el item en mano (no hacemos swap)
            return

        # Si no se puede apilar -> swap
        tmp_item, tmp_qty = slot.item, slot.quantity
        slot.item, slot.quantity = self.dragging_item, self.dragging_qty
        # mano ahora contiene lo que estaba
        self.dragging_item, self.dragging_qty = tmp_item, tmp_qty
        self.drag_origin_index = index  # origen pasa a ser el nuevo slot (para siguiente release)

    def _cancel_drag(self) -> None:
        self.dragging_item = None
        self.dragging_qty = 0
        self.drag_origin_index = None
