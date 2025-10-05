# -*- coding: utf-8 -*-
# ==============================================================================
# 🎯 BD_Aeterna_app.py / Aeterna_FINAL.py - PUNTO DE ENTRADA BIMODAL
# ==============================================================================

import sys
import json
import csv
import os
from datetime import datetime, timedelta

# Importamos la clase principal
from data_sources.drought.zone_model import CropZone 

# ==============================================================================
# 🌳 DEFINICIÓN DE LAS ZONAS DE CULTIVO (Mapeo de Abreviación a FIPS)
# ==============================================================================
ZONAS_MAPEO = {
    "AK": {"name": "Alaska (Valle Matanuska-Susitna)", "fips_code": "02", "state_abbr": "AK"},
    "ND": {"name": "Dakota del Norte (Woodworth)", "fips_code": "38", "state_abbr": "ND"},
    "CA": {"name": "California (TEST DE SEQUIA)", "fips_code": "06", "state_abbr": "CA"}
}
zonas_proyecto = [CropZone(**data) for data in ZONAS_MAPEO.values()]


# ==============================================================================
# FUNCIÓN AUXILIAR: EXPORTAR CSV
# ==============================================================================
def exportar_a_csv(data_json_string, estado_abbr, fecha_target):
    """Toma el string JSON de un solo registro y lo guarda en CSV."""
    
    output_dir = 'output_consultas'
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        records = json.loads(data_json_string)
        if not records or "error" in records[0]:
            print("\n⚠️ No se puede exportar: La consulta no devolvió datos válidos.")
            return

        data = records[0]
        filename = f"{estado_abbr}_{fecha_target}_consulta.csv"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(data.keys())
            writer.writerow(data.values())

        print(f"\n✅ Exportación exitosa: Archivo guardado en '{filepath}'")

    except Exception as e:
        print(f"\n❌ Error durante la exportación a CSV: {e}")


# ==============================================================================
# 🚀 EJECUCIÓN PRINCIPAL (Manejo Bimodal de Argumentos)
# ==============================================================================
if __name__ == "__main__":
    
    # --- MODO 1: ACTUALIZACIÓN DE RANGO ANUAL (--update) ---
    if len(sys.argv) > 1 and sys.argv[1].lower() == '--update':
        
        print("\n--- INICIANDO MODO: ACTUALIZACIÓN DE BASE DE DATOS (RANGO ANUAL) ---")
        
        # Validación: Esperamos 3 argumentos: [script, --update, AÑO]
        if len(sys.argv) != 3:
            print("\n--- ERROR DE USO ---")
            print("Uso correcto para la actualización: python Aeterna_FINAL.py --update [AÑO_INICIO]")
            print("Ejemplo: python Aeterna_FINAL.py --update 2024")
            sys.exit(1)
            
        target_year_str = sys.argv[2]
        
        # 1. Validación y Cálculo de Fechas
        try:
            target_year = int(target_year_str)
            
            # Fecha de Inicio: 1 de Enero del año dado
            start_dt = datetime(target_year, 1, 1)
            start_date_mmddyyyy = start_dt.strftime('%m%d%Y')
            
            # Fecha de Fin: 31 de Diciembre del año dado
            # NOTA: Usamos 365 días, si el año es bisiesto (366 días) se ajustará la fecha final.
            end_dt = datetime(target_year, 12, 31)
            end_date_mmddyyyy = end_dt.strftime('%m%d%Y')

        except ValueError:
            print(f"\n❌ Error: El argumento '{target_year_str}' no es un año válido (ej. 2024).")
            sys.exit(1)
            
        print(f"Rango anual a actualizar: Desde {start_date_mmddyyyy} hasta {end_date_mmddyyyy}.")
        
        # 2. Ejecutar la actualización para TODAS las zonas
        for zona in zonas_proyecto:
            # Los métodos run_full_range_update en zone_model.py deben esperar MMDDYYYY
            zona.run_full_range_update(start_date_mmddyyyy, end_date_mmddyyyy)
            
        print("\n--- PROCESO DE ACTUALIZACIÓN DE RANGO ANUAL COMPLETADO PARA TODAS LAS ZONAS ---")
    
    # --- MODO 2: CONSULTA DE PROXIMIDAD (ABR+FECHA) ---
    elif len(sys.argv) == 2:
        
        print("\n--- INICIANDO MODO: CONSULTA RÁPIDA DE PROXIMIDAD ---")

        entrada_usuario = sys.argv[1].upper()
        abbr_target = entrada_usuario[:2] 
        fecha_target = entrada_usuario[2:] 

        # Validación de la entrada (se mantiene igual)
        if abbr_target not in ZONAS_MAPEO or len(fecha_target) != 8:
            print("\n--- ERROR DE USO ---")
            print("Uso correcto para consulta: python Aeterna_FINAL.py [ABR+FECHA]")
            print("Ejemplo: python Aeterna_FINAL.py CA05182022")
            print("Abreviaciones válidas: AK, ND, CA.")
            sys.exit(1)
        
        try:
            datetime.strptime(fecha_target, '%m%d%Y')
        except ValueError:
            print(f"\n❌ Error: El formato de fecha '{fecha_target}' es inválido. Use MMDDYYYY.")
            sys.exit(1)

        # Localizar la Zona y Ejecutar la Consulta (se mantiene igual)
        zona_info = ZONAS_MAPEO[abbr_target]
        zona_consulta = next(zona for zona in zonas_proyecto if zona.fips_code == zona_info["fips_code"])

        print(f"Zona: {zona_consulta.name} ({abbr_target})")
        print(f"Fecha objetivo: {fecha_target}")
        
        try:
            json_output = zona_consulta.get_consolidated_by_proximity(fecha_target)
            
            print("\n✅ Datos consolidados por proximidad en JSON:")
            print(json_output)
            
            exportar_a_csv(json_output, abbr_target, fecha_target)
            
        except Exception as e:
            print(f"\n❌ Error catastrófico durante la consulta: {e}")

    # --- MODO 3: ERROR DE ARGUMENTOS ---
    else:
        print("\n--- ERROR DE USO: MODO INVÁLIDO ---")
        print("Para ACTUALIZAR la base de datos (rango anual): python Aeterna_FINAL.py --update [AÑO]")
        print("Para CONSULTAR un dato: python Aeterna_FINAL.py ABRMMDDYYYY")
        sys.exit(1)
        
    sys.exit(0)