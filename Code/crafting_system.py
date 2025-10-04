# crafting_system.py
# Sistema de crafteo para mesa de trabajo
from __future__ import annotations
from typing import List, Dict, Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from inventory import Inventory

# ==================== RECETAS DE CRAFTEO ====================
# Formato: "item_resultado": (cantidad_resultado, [(item_requerido, cantidad), ...])
# 
# EJEMPLOS DE CÃ"MO AGREGAR NUEVAS RECETAS:
# 
# "planks": (4, [("log", 1)]),  # 1 tronco → 4 tablas
# "rope": (1, [("leaves", 10)]),  # 10 hojas → 1 soga
# "chest_wood": (1, [("planks", 8), ("iron_ingot", 2)]),  # 8 tablas + 2 lingotes hierro → 1 cofre
#
# Para agregar una nueva receta:
# 1. Verifica que los items existan en items_registry.py
# 2. Agrega una lÃ­nea siguiendo el formato arriba
# 3. El primer valor es el item resultante (debe existir en items_registry)
# 4. El segundo valor es la cantidad que se produce
# 5. El tercer valor es una lista de tuplas (item_requerido, cantidad_requerida)

CRAFTING_RECIPES: Dict[str, Tuple[int, List[Tuple[str, int]]]] = {
    # Procesamiento básico
    "planks": (4, [("log", 1)]),
    "planks": (2, [("log_small", 1)]),
    
    # Herramientas básicas
    "rope": (1, [("leaves", 10)]),
    "rope_fiber": (1, [("leaves", 8)]),
    "stake_wood": (4, [("wood_branch", 2)]),
    
    # Herramientas mejoradas
    "hoe_wood_improv": (1, [("wood_branch", 3), ("rope", 1)]),
    "pick_wood_improv": (1, [("wood_branch", 3), ("rope", 1)]),
    "shovel_wood": (1, [("wood_branch", 2), ("planks", 1)]),
    "knife_wood": (1, [("wood_branch", 1), ("planks", 1)]),
    "rake_wood": (1, [("wood_branch", 2), ("rope", 1)]),
    
    # Herramientas de piedra
    "knife_stone": (1, [("rock", 2), ("rope", 1)]),
    "shovel_stone": (1, [("rock", 2), ("wood_branch", 1)]),
    
    # Recipientes
    "bowl_wood": (1, [("planks", 2)]),
    "bowl_stone": (1, [("rock", 3)]),
    "jar_small": (1, [("glass", 2)]),
    "jar_medium": (1, [("glass", 3)]),
    "jar_large": (1, [("glass", 4)]),
    
    # Estructuras
    "chest_wood": (1, [("planks", 8)]),
    "workbench": (1, [("planks", 4), ("log", 2)]),
    "bed": (1, [("planks", 6), ("leaves", 20)]),
    
    # Fertilizantes
    "bone_meal": (2, [("bone", 1)]),
    "fert_1": (1, [("bone_meal", 2), ("leaves", 5)]),
    
    # Iluminación
    "candle": (2, [("honeycomb_fragment", 1), ("rope_fiber", 1)]),
    
    # Transporte
    "basket": (1, [("wood_branch", 6), ("rope", 2)]),
    "wheelbarrow": (1, [("planks", 4), ("iron_ingot", 2), ("rope", 1)]),
}


class CraftingSystem:
    """Sistema de crafteo para mesa de trabajo"""
    
    def __init__(self):
        self.is_open = False
        self.selected_recipe: Optional[str] = None
        self.scroll_offset = 0
    
    def toggle(self):
        """Abre/cierra el menú de crafteo"""
        self.is_open = not self.is_open
        if not self.is_open:
            self.selected_recipe = None
    
    def can_craft(self, recipe_id: str, inventory: Inventory) -> bool:
        """Verifica si se puede craftear una receta"""
        if recipe_id not in CRAFTING_RECIPES:
            return False
        
        _, requirements = CRAFTING_RECIPES[recipe_id]
        
        for item_id, required_qty in requirements:
            available = inventory.count_item(item_id)
            if available < required_qty:
                return False
        
        return True
    
    def craft_item(self, recipe_id: str, inventory: Inventory) -> bool:
        """Intenta craftear un item"""
        if not self.can_craft(recipe_id, inventory):
            return False
        
        result_qty, requirements = CRAFTING_RECIPES[recipe_id]
        
        # Consumir materiales
        for item_id, required_qty in requirements:
            inventory.remove_item(item_id, required_qty)
        
        # Agregar resultado
        inventory.add_item(recipe_id, result_qty)
        return True
    
    def get_available_recipes(self, inventory: Inventory) -> List[str]:
        """Retorna lista de recetas que se pueden craftear"""
        available = []
        for recipe_id in CRAFTING_RECIPES.keys():
            if self.can_craft(recipe_id, inventory):
                available.append(recipe_id)
        return available
    
    def get_recipe_info(self, recipe_id: str) -> Optional[Dict]:
        """Obtiene información de una receta"""
        if recipe_id not in CRAFTING_RECIPES:
            return None
        
        result_qty, requirements = CRAFTING_RECIPES[recipe_id]
        return {
            "result": recipe_id,
            "result_qty": result_qty,
            "requirements": requirements
        }


# Exportar
__all__ = ["CraftingSystem", "CRAFTING_RECIPES"]