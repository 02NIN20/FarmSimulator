# furnace_system.py
# Sistema de horno con combustible para fundición y cocción
from __future__ import annotations
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from inventory import Inventory

# ==================== COMBUSTIBLES ====================
# Formato: "item_id": tiempo_combustión_segundos
# 
# Los combustibles válidos son items que pueden quemarse
COMBUSTIBLES: Dict[str, float] = {
    "leaves": 5.0,           # Hojas: 5 segundos
    "wood_branch": 8.0,      # Rama: 8 segundos
    "log_small": 15.0,       # Tronco pequeño: 15 segundos
    "log": 25.0,             # Tronco: 25 segundos
    "planks": 12.0,          # Tablas: 12 segundos
    "ore_coal": 40.0,        # Carbón: 40 segundos
    "carbon_element": 50.0,  # Carbono puro: 50 segundos
}

# ==================== RECETAS DE FUNDICIÃ"N ====================
# Formato: "item_entrada": ("item_salida", cantidad_salida, tiempo_procesamiento)
# 
# EJEMPLOS DE CÃ"MO AGREGAR NUEVAS RECETAS DE FUNDICIÃ"N:
# 
# "ore_iron": ("iron_ingot", 1, 20.0),  # Mena de hierro → 1 lingote (20 seg)
# "clay": ("glass", 1, 15.0),  # Arcilla → 1 vidrio (15 seg)
# "meat_chicken_breast": ("meat_chicken_breast", 1, 10.0),  # Cocinar pollo (10 seg)
#
# Para agregar una nueva receta de fundición:
# 1. Verifica que los items existan en items_registry.py
# 2. Agrega una línea con el formato: "item_entrada": ("item_salida", cantidad, tiempo_segundos)
# 3. El item de entrada es lo que se pone en el horno
# 4. El item de salida es lo que se obtiene
# 5. La cantidad es cuántos items de salida se producen
# 6. El tiempo es cuántos segundos tarda el proceso

SMELTING_RECIPES: Dict[str, Tuple[str, int, float]] = {
    # Fundición de minerales
    "ore_iron": ("iron_ingot", 1, 20.0),
    "ore_copper": ("copper_ingot", 1, 18.0),
    "ore_steel": ("steel_ingot", 1, 25.0),
    
    # Vidrio y cerámica
    "clay": ("glass", 1, 15.0),
    
    # Cocción de alimentos
    "meat_chicken_breast": ("meat_chicken_breast", 1, 10.0),  # Nota: mismo item, pero "cocido"
    "meat_beef_steak": ("meat_beef_steak", 1, 12.0),
    "meat_pork_chop": ("meat_pork_chop", 1, 11.0),
    "meat_fish_fillet": ("meat_fish_fillet", 1, 8.0),
    
    # Procesamiento especial
    "rock": ("glass", 1, 30.0),  # Derretir roca → vidrio
    "honeycomb": ("honeycomb_fragment", 4, 5.0),  # Procesar panal
}


class FurnaceSystem:
    """Sistema de horno con combustible"""
    
    def __init__(self):
        self.is_open = False
        
        # Estado del horno
        self.fuel_time_remaining = 0.0  # Tiempo de combustible restante
        self.process_time_elapsed = 0.0  # Tiempo transcurrido procesando
        self.process_time_needed = 0.0   # Tiempo total necesario para procesar
        
        # Items en el horno
        self.input_item: Optional[str] = None
        self.input_qty = 0
        self.fuel_item: Optional[str] = None
        self.fuel_qty = 0
        self.output_item: Optional[str] = None
        self.output_qty = 0
        
        self.is_processing = False
    
    def toggle(self):
        """Abre/cierra el menú del horno"""
        self.is_open = not self.is_open
    
    def add_input(self, item_id: str, inventory: Inventory) -> bool:
        """Agrega un item para procesar"""
        if item_id not in SMELTING_RECIPES:
            return False
        
        if self.input_item and self.input_item != item_id:
            return False  # Ya hay otro item
        
        if inventory.count_item(item_id) <= 0:
            return False
        
        inventory.remove_item(item_id, 1)
        
        if self.input_item == item_id:
            self.input_qty += 1
        else:
            self.input_item = item_id
            self.input_qty = 1
        
        return True
    
    def add_fuel(self, item_id: str, inventory: Inventory) -> bool:
        """Agrega combustible al horno"""
        if item_id not in COMBUSTIBLES:
            return False
        
        if self.fuel_item and self.fuel_item != item_id:
            return False  # Ya hay otro combustible
        
        if inventory.count_item(item_id) <= 0:
            return False
        
        inventory.remove_item(item_id, 1)
        
        if self.fuel_item == item_id:
            self.fuel_qty += 1
        else:
            self.fuel_item = item_id
            self.fuel_qty = 1
        
        return True
    
    def remove_output(self, inventory: Inventory) -> bool:
        """Remueve items procesados del horno"""
        if not self.output_item or self.output_qty <= 0:
            return False
        
        inventory.add_item(self.output_item, self.output_qty)
        self.output_item = None
        self.output_qty = 0
        return True
    
    def update(self, dt: float):
        """Actualiza el estado del horno"""
        # Si no hay input o no hay combustible, no procesar
        if not self.input_item or self.input_qty <= 0:
            self.is_processing = False
            return
        
        # Consumir combustible si es necesario
        if self.fuel_time_remaining <= 0.0:
            if self.fuel_item and self.fuel_qty > 0:
                self.fuel_time_remaining = COMBUSTIBLES.get(self.fuel_item, 0.0)
                self.fuel_qty -= 1
                if self.fuel_qty <= 0:
                    self.fuel_item = None
            else:
                self.is_processing = False
                return
        
        # Iniciar procesamiento si es necesario
        if not self.is_processing:
            recipe = SMELTING_RECIPES.get(self.input_item)
            if recipe:
                output_id, output_qty, process_time = recipe
                self.process_time_needed = process_time
                self.process_time_elapsed = 0.0
                self.is_processing = True
        
        # Procesar
        if self.is_processing:
            self.fuel_time_remaining -= dt
            self.process_time_elapsed += dt
            
            # Completar procesamiento
            if self.process_time_elapsed >= self.process_time_needed:
                recipe = SMELTING_RECIPES.get(self.input_item)
                if recipe:
                    output_id, output_qty, _ = recipe
                    
                    # Agregar a output
                    if self.output_item == output_id or not self.output_item:
                        self.output_item = output_id
                        self.output_qty += output_qty
                    
                    # Consumir input
                    self.input_qty -= 1
                    if self.input_qty <= 0:
                        self.input_item = None
                    
                    # Resetear procesamiento
                    self.is_processing = False
                    self.process_time_elapsed = 0.0
    
    def get_progress(self) -> float:
        """Retorna el progreso del procesamiento (0.0 a 1.0)"""
        if not self.is_processing or self.process_time_needed <= 0:
            return 0.0
        return min(1.0, self.process_time_elapsed / self.process_time_needed)
    
    def get_fuel_progress(self) -> float:
        """Retorna el progreso del combustible actual (0.0 a 1.0)"""
        if not self.fuel_item:
            return 0.0
        max_fuel = COMBUSTIBLES.get(self.fuel_item, 1.0)
        return min(1.0, self.fuel_time_remaining / max_fuel)


# Exportar
__all__ = ["FurnaceSystem", "SMELTING_RECIPES", "COMBUSTIBLES"]