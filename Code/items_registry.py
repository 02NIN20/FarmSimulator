# items_registry.py
# Catálogo de ítems del juego. No importamos Item aquí para evitar ciclos.
# Devolvemos tuplas con: (item_id, name, description, Color, stackable, max_stack)

from __future__ import annotations
from typing import Iterable, List, Tuple
from pyray import Color

# ---------- Utilidades ----------

def _mat(id_: str, name: str, desc: str, col: Tuple[int,int,int], stack: bool = True, maxs: int = 99):
    r,g,b = col
    return (id_, name, desc, Color(r,g,b,255), stack, maxs)

def _tool(id_: str, name: str, desc: str, col: Tuple[int,int,int]):
    # Herramientas no apilables
    return _mat(id_, name, desc, col, stack=False, maxs=1)

def _pair_crop(base_id: str, name: str, seed_col: Tuple[int,int,int], prod_col: Tuple[int,int,int]):
    # Genera (semilla, producto) para un cultivo
    seed = _mat(f"seed_{base_id}", f"Semilla de {name}", f"Semilla para cultivar {name.lower()}", seed_col, True, 99)
    prod = _mat(base_id, name, f"{name} cosechada", prod_col, True, 99)
    return [seed, prod]

# ---------- Ítems “core” pedidos ----------

EXTRA_BASE_ITEMS: List[Tuple] = [
    _tool("bucket_water", "Cubeta de agua", "Recipiente con agua", (100,170,255)),
    _tool("hoe_wood_improv", "Azadón improvisado de madera", "Herramienta básica para labrar", (160,120,70)),
    _tool("hoe_wood", "Azadón de madera", "Herramienta para labrar", (150,110,60)),
    _tool("hoe_copper", "Azadón de cobre", "Herramienta resistente para labrar", (200,110,70)),
    _tool("hoe_iron", "Azadón de hierro", "Herramienta de labranza", (140,140,150)),
    _tool("hoe_steel", "Azadón de acero", "Herramienta de labranza avanzada", (120,130,140)),

    _tool("pick_wood_improv", "Pico improvisado de madera", "Pico básico", (160,120,70)),
    _tool("pick_copper", "Pico de cobre", "Para minería ligera", (210,120,80)),
    _tool("pick_iron", "Pico de hierro", "Para minería", (140,140,150)),
    _tool("pick_steel", "Pico de acero", "Para minería pesada", (120,130,140)),

    _mat("bone", "Hueso", "Hueso animal", (230,230,210)),
    _mat("bone_meal", "Hueso molido", "Enmienda/fertilizante fósforo", (220,210,180)),

    # Suelos por zona (esc. 2–4)
    _mat("soil_alaska", "Tierra boreal (Alaska)", "Suelo local de Matanuska–Susitna", (110,120,95)),
    _mat("soil_ppr", "Tierra pradera (Dakota del Norte)", "Suelo local PPR (Woodworth)", (120,115,85)),
    _mat("soil_michigan", "Tierra bosque húmedo (Michigan)", "Suelo local Leelanau", (105,125,95)),

    _mat("ore_coal", "Mena de carbón", "Fragmento de carbón", (40,40,40)),
    _mat("wood_branch", "Rama de madera", "Rama pequeña", (150,110,70)),
    _mat("rope", "Soga", "Cuerda trenzada", (200,180,120)),
    _mat("log_small", "Sección de tronco (pequeña)", "Corte de tronco", (120,85,50)),
    _mat("log", "Sección de tronco", "Tronco para procesar", (110,80,45)),
    _mat("rock", "Roca", "Piedra común", (120,120,120)),
    _mat("ore_iron", "Mena de hierro", "Mineral de hierro", (110,110,115)),
    _mat("ore_steel", "Mena de acero", "Aleación recuperada", (125,130,135)),
    _mat("ore_copper", "Mena de cobre", "Mineral de cobre", (200,120,70)),

    _tool("furnace", "Horno", "Horno para fundición", (100,100,110)),
    _tool("workbench", "Taller de trabajo", "Mesa de crafteo", (120,90,60)),
    _tool("chest_wood", "Cofre de madera", "Almacenamiento común", (125,90,60)),
    _tool("bed", "Cama", "Para dormir", (200,180,170)),

    _mat("jar_small", "Frasco pequeño", "Contenedor de vidrio (pequeño)", (190,230,250)),
    _mat("jar_medium", "Frasco mediano", "Contenedor de vidrio (mediano)", (175,220,245)),
    _mat("jar_large", "Frasco grande", "Contenedor de vidrio (grande)", (160,210,240)),
    _mat("planks", "Tablas", "Tabla de madera procesada", (160,120,70)),
    _tool("anvil", "Yunque", "Forja y conformado", (90,95,110)),
    _mat("glass", "Vidrio", "Vidrio elaborado", (200,240,255)),
    _mat("clay", "Arcilla", "Arcilla para cerámica", (180,120,90)),

    _mat("chicken_egg", "Huevos de gallina", "Alimento/proceso", (245,245,210)),
    _mat("bowl_wood", "Cuenco de madera", "Recipiente común", (150,110,70)),
    _mat("bowl_stone", "Cuenco de piedra", "Recipiente pesado", (130,130,130)),

    _tool("knife_wood", "Cuchillo de madera", "Cuchillo básico", (160,120,70)),
    _tool("knife_stone", "Cuchillo de piedra", "Cuchillo rudimentario", (120,120,120)),
    _tool("knife_iron", "Cuchillo de hierro", "Cuchillo resistente", (140,140,150)),
    _tool("knife_steel", "Cuchillo de acero", "Cuchillo afilado", (120,130,140)),

    _mat("salt", "Sal", "Cloruro sódico", (235,235,235)),

    # Cortes de carne
    _mat("meat_chicken_breast", "Pechuga de pollo", "Carne de pollo", (225,120,110)),
    _mat("meat_beef_steak", "Bistec de res", "Carne de res", (190,60,60)),
    _mat("meat_pork_chop", "Chuleta de cerdo", "Carne de cerdo", (230,140,140)),
    _mat("meat_fish_fillet", "Filete de pescado", "Carne de pescado", (190,210,230)),

    _mat("leaves", "Hojas", "Biomasa vegetal", (90,140,70)),

    _tool("shovel_wood", "Pala de madera", "Para cavar", (160,120,70)),
    _tool("shovel_stone", "Pala de piedra", "Para cavar", (120,120,120)),
    _tool("shovel_iron", "Pala de hierro", "Para cavar", (140,140,150)),
    _tool("shovel_steel", "Pala de acero", "Para cavar", (120,130,140)),

    _mat("rope_fiber", "Cuerda", "Cuerda de fibras", (200,180,120)),
    _mat("stake_wood", "Estacas de madera", "Para cercado/soporte", (150,110,70)),
    _mat("stake_iron", "Estacas de hierro", "Para cercado/soporte", (140,140,150)),

    _tool("hoehead_weeder_wood", "Escardilla de madera", "Control de malezas", (160,120,70)),
    _tool("hoehead_weeder_iron", "Escardilla de hierro", "Control de malezas", (140,140,150)),
    _tool("hoehead_weeder_copper", "Escardilla de cobre", "Control de malezas", (200,110,70)),

    _tool("rake_wood", "Rastrillo de madera", "Nivelado/superficie", (160,120,70)),
    _tool("rake_iron", "Rastrillo de hierro", "Nivelado/superficie", (140,140,150)),
    _tool("rake_copper", "Rastrillo de cobre", "Nivelado/superficie", (200,110,70)),

    _tool("pruner", "Tijeras para podar", "Poda de ramas/tallos", (110,150,120)),

    _tool("saw_copper", "Serrucho de cobre", "Corte de madera", (200,120,70)),
    _tool("saw_iron", "Serrucho de hierro", "Corte de madera", (140,140,150)),
    _tool("saw_steel", "Serrucho de acero", "Corte de madera", (120,130,140)),

    _mat("carbon_element", "Carbono", "Elemento carbono", (60,60,60)),
    _tool("wheelbarrow", "Carretilla", "Transporte manual", (90,90,90)),
    _tool("basket", "Canasta", "Transporte y recolección", (170,130,90)),

    _mat("fert_1", "Fertilizante 1", "Fertilizante (básico)", (160,140,90)),
    _mat("fert_2", "Fertilizante 2", "Fertilizante (balanceado)", (150,160,90)),
    _mat("fert_3", "Fertilizante 3", "Fertilizante (alto rendimiento)", (140,170,90)),

    _tool("bucket_milk", "Cubeta de leche", "Recipiente con leche", (240,240,230)),
    _tool("bucket_empty", "Cubeta", "Recipiente vacío", (180,180,180)),

    _mat("candle", "Vela", "Fuente de luz simple", (255,240,180)),
    _mat("honey", "Miel de abejas", "Producto apícola", (240,200,80)),
    _mat("honeycomb", "Panal de abejas", "Cera y miel", (220,180,70)),
    _mat("honeycomb_fragment", "Fragmento de panal", "Fragmento ceroso", (210,170,65)),
]

# ---------- Cultivos (semilla + producto) ----------
CROP_PAIRS: List[List[Tuple]] = [
    _pair_crop("potato", "Patata", (240,210,110), (210,170,90)),
    _pair_crop("cabbage", "Col repollo", (190,220,150), (120,190,120)),
    _pair_crop("carrot", "Zanahoria", (240,170,90), (230,120,50)),
    _pair_crop("spring_barley", "Cebada de primavera", (210,210,160), (200,180,120)),
    _pair_crop("raspberry_ht", "Frambuesa en túnel alto", (230,150,170), (210,70,110)),
    _pair_crop("kale", "Col rizada (kale)", (170,210,170), (110,160,110)),
    _pair_crop("spring_wheat", "Trigo de primavera", (230,210,150), (220,200,120)),
    _pair_crop("sunflower", "Girasol", (240,210,70), (230,200,60)),
    _pair_crop("canola", "Canola", (215,215,120), (205,205,90)),
    _pair_crop("soy", "Soja", (200,220,180), (190,210,160)),
    _pair_crop("field_pea", "Guisante seco (field pea)", (190,230,190), (130,200,140)),
    _pair_crop("malting_barley", "Cebada cervecera", (210,210,160), (200,180,120)),
    _pair_crop("tart_cherry", "Cereza ácida (tart cherry)", (230,120,120), (210,60,60)),
    _pair_crop("apple", "Manzana", (220,240,170), (220,60,60)),
    _pair_crop("blueberry", "Arándano (blueberry)", (180,200,240), (80,100,200)),
    _pair_crop("cold_hybrid_grape", "Uva vinífera híbrida fría", (190,200,220), (150,100,170)),
    _pair_crop("asparagus", "Espárrago", (190,220,170), (110,170,110)),
    _pair_crop("pickling_cucumber", "Pepinillo para encurtido", (190,220,180), (110,180,120)),
]

# ---------- Ítems extra (ciencia, electrónica, metalurgia, mecánica, etc.) ----------

SCI_TECH_ITEMS: List[Tuple] = [
    _mat("soil_ph_meter", "Medidor pH de suelo", "Sonda pH portátil", (120,180,120)),
    _mat("soil_moisture_sensor", "Sensor de humedad de suelo", "Sonda volumétrica", (120,160,200)),
    _mat("thermometer", "Termómetro", "Medición de temperatura", (200,200,220)),
    _mat("hygrometer", "Higrómetro", "Medición de humedad ambiente", (190,210,230)),
    _mat("anemometer", "Anemómetro", "Velocidad del viento", (170,190,210)),

    _mat("copper_wire", "Cable de cobre", "Conductor eléctrico", (210,120,70)),
    _mat("pcb", "Placa PCB", "Placa de circuito impreso", (70,140,100)),
    _mat("microcontroller", "Microcontrolador", "Control de sensores/actuadores", (90,110,130)),
    _mat("battery", "Batería", "Almacenamiento eléctrico", (80,80,90)),
    _mat("solar_panel", "Panel solar", "Generación eléctrica", (30,60,120)),
    _mat("resistor", "Resistor", "Componente electrónico", (160,120,80)),
    _mat("capacitor", "Capacitor", "Componente electrónico", (100,140,180)),
    _mat("transistor", "Transistor", "Componente semiconductor", (120,120,160)),
    _mat("silicon_wafer", "Oblea de silicio", "Semiconductor base", (200,200,200)),

    _mat("flux", "Fundente", "Ayuda a soldadura y fundición", (200,180,120)),
    _mat("welding_rod", "Varilla de soldadura", "Aporte metálico", (150,150,160)),
    _mat("crucible_ceramic", "Crisol cerámico", "Fusión de metales", (180,150,120)),

    _mat("iron_ingot", "Lingote de hierro", "Metal procesado", (150,150,160)),
    _mat("steel_ingot", "Lingote de acero", "Aleación procesada", (130,140,150)),
    _mat("copper_ingot", "Lingote de cobre", "Metal procesado", (210,120,70)),
    _mat("aluminum_ingot", "Lingote de aluminio", "Metal ligero", (200,200,210)),
    _mat("titanium_ingot", "Lingote de titanio", "Metal de alta resistencia", (170,180,190)),
    _mat("nickel_ingot", "Lingote de níquel", "Metal resistente a corrosión", (160,170,180)),
    _mat("cobalt_ingot", "Lingote de cobalto", "Metal duro", (120,130,170)),

    _mat("bearing", "Rodamiento", "Elemento de máquina", (110,110,120)),
    _mat("gear", "Engranaje", "Transmisión mecánica", (100,100,110)),
    _mat("belt", "Banda", "Transmisión por correa", (80,80,80)),
]

# ---------- Iterador público ----------

def iter_all_items() -> Iterable[Tuple[str,str,str,Color,bool,int]]:
    # Base
    for it in EXTRA_BASE_ITEMS:
        yield it
    # Cultivos (semilla y producto)
    for pair in CROP_PAIRS:
        for it in pair:
            yield it
    # Ciencia/tecnología
    for it in SCI_TECH_ITEMS:
        yield it
