
# verificar_dato.py
import json
import os
import sys

# Ajusta el path para importar desde el directorio correcto
# Asumimos que data_sources está en el mismo nivel que este script
sys.path.append(os.path.join(os.path.dirname(__file__), 'data_sources')) 
from drought.zone_model import CropZone 

# Zona que debería haberse actualizado
ZONA_NAME = "California (TEST DE SEQUIA)"
STATE_ABBR = "CA"
FIPS_CODE = "06"

# Rango de fechas a consultar (para el año actualizado)
START_DATE = "01012024"
END_DATE = "12312024"

print("\n--- VERIFICANDO DATO DE SEQUÍA GUARDADO EN LA DB ---")
zona_test = CropZone(name=ZONA_NAME, state_abbr=STATE_ABBR, fips_code=FIPS_CODE)

# Usamos get_data_by_date_range para obtener los datos que se acaban de guardar
resultado_json = zona_test.get_data_by_date_range(START_DATE, END_DATE)

print(f"\n✅ Primer registro de sequía encontrado para {ZONA_NAME} en 2024:\n")

try:
    parsed_json = json.loads(resultado_json)
    if isinstance(parsed_json, list) and parsed_json:
        # Mostramos el primer registro completo (el dato)
        print(json.dumps(parsed_json[0], indent=4)) 
        print(f"\n... y {len(parsed_json)-1} registros más guardados.")
    else:
        # Muestra el mensaje de error si no hay datos
        print("❌ La consulta no devolvió datos. Es probable que la API no funcionara o no hay datos en ese rango.")
        print(resultado_json)
except Exception as e:
    print(f"❌ Error al procesar el resultado: {e}")
    print(resultado_json)