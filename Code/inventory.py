# inventory.py

from __future__ import annotations
from typing import Dict, Optional
from pyray import *

class Item:
    """Representa un item en el inventario."""
    def __init__(self, item_id: str, name: str, description: str, icon_color: Color, stackable: bool = True, max_stack: int = 99):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.icon_color = icon_color
        self.stackable = stackable
        self.max_stack = max_stack

class InventorySlot:
    """Representa un slot del inventario."""
    def __init__(self):
        self.item: Optional[Item] = None
        self.quantity: int = 0
    
    def is_empty(self) -> bool:
        return self.item is None or self.quantity <= 0
    
    def add_item(self, item: Item, amount: int = 1) -> int:
        """Añade items al slot. Retorna la cantidad que NO pudo añadir (sobrante)."""
        if self.is_empty():
            self.item = item
            self.quantity = min(amount, item.max_stack)
            return max(0, amount - self.quantity)
        
        if self.item.item_id == item.item_id and item.stackable:
            space_left = item.max_stack - self.quantity
            added = min(space_left, amount)
            self.quantity += added
            return amount - added
        
        return amount
    
    def remove_item(self, amount: int = 1) -> int:
        """Remueve items del slot. Retorna la cantidad removida."""
        removed = min(amount, self.quantity)
        self.quantity -= removed
        if self.quantity <= 0:
            self.item = None
            self.quantity = 0
        return removed

class Inventory:
    """Sistema de inventario con soporte de arrastrar y soltar (drag & drop)."""
    def __init__(self, rows: int = 4, cols: int = 10):
        self.rows = rows
        self.cols = cols
        self.total_slots = rows * cols
        self.slots: list[InventorySlot] = [InventorySlot() for _ in range(self.total_slots)]
        self.selected_slot: int = -1
        self.is_open: bool = False
        
        # Catálogo de items (puedes extenderlo)
        self.item_database: Dict[str, Item] = {
            "seed_corn": Item("seed_corn", "Semilla de Maíz", "Semilla para cultivar maíz", Color(255, 220, 100, 255)),
            "seed_wheat": Item("seed_wheat", "Semilla de Trigo", "Semilla para cultivar trigo", Color(220, 180, 80, 255)),
            "seed_tomato": Item("seed_tomato", "Semilla de Tomate", "Semilla para cultivar tomate", Color(220, 50, 50, 255)),
            "corn": Item("corn", "Maíz", "Maíz cosechado", Color(255, 230, 80, 255)),
            "wheat": Item("wheat", "Trigo", "Trigo cosechado", Color(240, 200, 100, 255)),
            "tomato": Item("tomato", "Tomate", "Tomate cosechado", Color(255, 60, 60, 255)),
            "water": Item("water", "Agua", "Para regar cultivos", Color(100, 180, 255, 255)),
            "fertilizer": Item("fertilizer", "Fertilizante", "Mejora el crecimiento", Color(120, 90, 60, 255)),
        }

        # --- Estado para Drag & Drop ---
        self.dragging: bool = False
        self.drag_origin: int = -1
        self.drag_item: Optional[Item] = None
        self.drag_qty: int = 0

    # ---------- API básica ----------
    def toggle(self):
        """Abre o cierra el inventario."""
        self.is_open = not self.is_open
        if not self.is_open:
            self.selected_slot = -1
            self._cancel_drag()
    
    def add_item(self, item_id: str, amount: int = 1) -> bool:
        """Añade un item al inventario. Retorna True si se pudo añadir todo."""
        if item_id not in self.item_database:
            return False
        
        item = self.item_database[item_id]
        remaining = amount
        
        # Primero llena stacks existentes
        if item.stackable:
            for slot in self.slots:
                if not slot.is_empty() and slot.item.item_id == item_id:
                    remaining = slot.add_item(item, remaining)
                    if remaining <= 0:
                        return True
        
        # Luego usa slots vacíos
        for slot in self.slots:
            if slot.is_empty():
                remaining = slot.add_item(item, remaining)
                if remaining <= 0:
                    return True
        
        return remaining <= 0
    
    def remove_item(self, item_id: str, amount: int = 1) -> bool:
        """Remueve un item del inventario. Retorna True si se pudo remover todo."""
        remaining = amount
        
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                removed = slot.remove_item(remaining)
                remaining -= removed
                if remaining <= 0:
                    return True
        
        return remaining <= 0
    
    def has_item(self, item_id: str, amount: int = 1) -> bool:
        """Verifica si el inventario tiene suficiente cantidad de un item."""
        total = 0
        for slot in self.slots:
            if not slot.is_empty() and slot.item.item_id == item_id:
                total += slot.quantity
        return total >= amount

    # ---------- Helpers UI ----------
    def get_slot_at_position(self, mx: int, my: int, inv_x: int, inv_y: int, slot_size: int, padding: int) -> int:
        """Retorna el índice del slot en la posición del mouse, o -1 si no hay ninguno."""
        for i in range(self.total_slots):
            row = i // self.cols
            col = i % self.cols
            sx = inv_x + col * (slot_size + padding)
            sy = inv_y + row * (slot_size + padding)
            
            if mx >= sx and mx <= sx + slot_size and my >= sy and my <= sy + slot_size:
                return i
        return -1

    def _cancel_drag(self):
        self.dragging = False
        self.drag_origin = -1
        self.drag_item = None
        self.drag_qty = 0

    def _pickup_from_slot(self, idx: int):
        """Levanta (toma) el stack completo de un slot para arrastrarlo."""
        if idx < 0 or idx >= self.total_slots:
            return
        slot = self.slots[idx]
        if slot.is_empty():
            return
        self.dragging = True
        self.drag_origin = idx
        self.drag_item = slot.item
        self.drag_qty = slot.quantity
        # Vaciar slot origen mientras arrastramos
        slot.item = None
        slot.quantity = 0

    def _drop_on_slot(self, idx: int):
        """
        Suelta el stack arrastrado sobre un slot.
        - Si el slot está vacío: move.
        - Si tiene el mismo item y stackea: merge (el sobrante vuelve al origen).
        - Si tiene item distinto: swap con el origen.
        """
        if not self.dragging or self.drag_item is None or self.drag_qty <= 0:
            return

        # Drop fuera de rango -> devolver al origen
        if idx < 0 or idx >= self.total_slots:
            origin = self.slots[self.drag_origin]
            _ = origin.add_item(self.drag_item, self.drag_qty)
            self._cancel_drag()
            return

        dest = self.slots[idx]

        # 1) Slot vacío -> mover todo
        if dest.is_empty():
            _ = dest.add_item(self.drag_item, self.drag_qty)
            self._cancel_drag()
            return

        # 2) Mismo item y stackeable -> merge
        if dest.item and dest.item.item_id == self.drag_item.item_id and self.drag_item.stackable:
            leftover = dest.add_item(self.drag_item, self.drag_qty)
            if leftover > 0:
                origin = self.slots[self.drag_origin]
                _ = origin.add_item(self.drag_item, leftover)
            self._cancel_drag()
            return

        # 3) Item distinto -> swap con origen
        origin = self.slots[self.drag_origin]
        dest_item, dest_qty = dest.item, dest.quantity
        dest.item, dest.quantity = self.drag_item, self.drag_qty
        origin.item, origin.quantity = dest_item, dest_qty
        self._cancel_drag()

    # ---------- Dibujo ----------
    def draw(self, screen_w: int, screen_h: int):
        """Dibuja la interfaz del inventario con soporte de arrastrar y soltar."""
        if not self.is_open:
            return
        
        # Fondo semi-transparente
        draw_rectangle(0, 0, screen_w, screen_h, Color(0, 0, 0, 180))
        
        # Panel del inventario
        slot_size = min(60, int(screen_w * 0.05))
        padding = max(4, int(slot_size * 0.1))
        
        inv_width = self.cols * (slot_size + padding) + padding
        inv_height = self.rows * (slot_size + padding) + padding + 80
        
        inv_x = (screen_w - inv_width) // 2
        inv_y = (screen_h - inv_height) // 2
        
        # Panel principal
        draw_rectangle(inv_x - 20, inv_y - 40, inv_width + 40, inv_height, Color(60, 50, 40, 255))
        draw_rectangle_lines(inv_x - 20, inv_y - 40, inv_width + 40, inv_height, Color(200, 180, 140, 255))
        
        # Título
        title_font = max(20, int(screen_h * 0.03))
        title_text = "INVENTARIO"
        title_width = measure_text(title_text, title_font)
        draw_text(title_text, inv_x + (inv_width - title_width) // 2, inv_y - 30, title_font, Color(255, 240, 200, 255))
        
        # Mouse
        mouse_pos = get_mouse_position()
        mx, my = int(mouse_pos.x), int(mouse_pos.y)
        hovered_slot = self.get_slot_at_position(mx, my, inv_x, inv_y, slot_size, padding)

        # --- Iniciar drag con click izquierdo sobre un slot con item ---
        if is_mouse_button_pressed(MOUSE_LEFT_BUTTON) and not self.dragging and hovered_slot >= 0:
            if not self.slots[hovered_slot].is_empty():
                self._pickup_from_slot(hovered_slot)
                self.selected_slot = -1  # limpiamos selección previa

        # --- Soltar stack (drop) al liberar click izquierdo ---
        if is_mouse_button_released(MOUSE_LEFT_BUTTON) and self.dragging:
            self._drop_on_slot(hovered_slot)

        # --- Dibujar slots ---
        for i in range(self.total_slots):
            row = i // self.cols
            col = i % self.cols
            sx = inv_x + col * (slot_size + padding)
            sy = inv_y + row * (slot_size + padding)
            
            # Color del slot
            slot_color = Color(80, 70, 60, 255)
            if i == hovered_slot and not self.dragging:
                slot_color = Color(100, 90, 80, 255)
            if i == self.selected_slot:
                slot_color = Color(120, 200, 255, 255)
            
            draw_rectangle(sx, sy, slot_size, slot_size, slot_color)
            draw_rectangle_lines(sx, sy, slot_size, slot_size, Color(40, 35, 30, 255))
            
            # Dibujar item si existe (nota: si es origen y estamos arrastrando, quedó vacío)
            slot = self.slots[i]
            if not slot.is_empty():
                icon_size = int(slot_size * 0.7)
                icon_x = sx + (slot_size - icon_size) // 2
                icon_y = sy + (slot_size - icon_size) // 2
                draw_rectangle(icon_x, icon_y, icon_size, icon_size, slot.item.icon_color)
                draw_rectangle_lines(icon_x, icon_y, icon_size, icon_size, BLACK)
                
                # Cantidad
                if slot.quantity > 1:
                    qty_text = str(slot.quantity)
                    qty_font = max(12, int(slot_size * 0.25))
                    draw_text(qty_text, sx + slot_size - measure_text(qty_text, qty_font) - 4, 
                              sy + slot_size - qty_font - 2, qty_font, WHITE)

        # --- Tooltip del item hovereado (ESTILO ANTERIOR restaurado) ---
        if not self.dragging and hovered_slot >= 0 and not self.slots[hovered_slot].is_empty():
            item = self.slots[hovered_slot].item
            tooltip_font = max(14, int(screen_h * 0.02))

            # Dimensiones y posición con límites de pantalla
            tooltip_w = max(200, measure_text(item.description, tooltip_font) + 20)
            tooltip_h = 60
            tooltip_x = min(mx + 15, screen_w - tooltip_w - 10)
            tooltip_y = min(my + 15, screen_h - tooltip_h - 10)

            # Fondo y borde ámbar (look & feel anterior)
            draw_rectangle(tooltip_x, tooltip_y, tooltip_w, tooltip_h, Color(40, 35, 30, 240))
            draw_rectangle_lines(tooltip_x, tooltip_y, tooltip_w, tooltip_h, Color(200, 180, 140, 255))

            # Título (ámbar claro) + descripción (blanco cálido)
            draw_text(item.name, tooltip_x + 10, tooltip_y + 8, tooltip_font + 2, Color(255, 230, 150, 255))
            draw_text(item.description, tooltip_x + 10, tooltip_y + 30, tooltip_font, Color(220, 220, 220, 255))

        # --- Sombra del item que se arrastra (siguiendo el mouse) ---
        if self.dragging and self.drag_item is not None and self.drag_qty > 0:
            icon_size = int(slot_size * 0.7)
            ix = mx - icon_size // 2
            iy = my - icon_size // 2
            draw_rectangle(ix, iy, icon_size, icon_size, self.drag_item.icon_color)
            draw_rectangle_lines(ix, iy, icon_size, icon_size, BLACK)
            if self.drag_qty > 1:
                qty_text = str(self.drag_qty)
                qty_font = max(12, int(slot_size * 0.25))
                draw_text(qty_text, ix + icon_size - measure_text(qty_text, qty_font) - 2,
                          iy + icon_size - qty_font - 2, qty_font, WHITE)