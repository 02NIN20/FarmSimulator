# data_sources/giovanni/giovanni_api.py (MODIFICADO)
# -*- coding: utf-8 -*-
import random
from datetime import datetime, timedelta

class GiovanniAPI:
    """Clase para simular la interacción con la API de Giovanni (Precipitación)."""
    
    BASE_URL = "https://giovanni.nasa.gov/api/data"  
    
    def __init__(self, fips_code, start_date, end_date):
        self.fips_code = fips_code 
        self.start_date = start_date # MMDDYYYY
        self.end_date = end_date     # MMDDYYYY
        print(f"  [GiovanniAPI] Inicializada para FIPS {fips_code}.")

    def fetch_range_data(self):
        """
        Simula la obtención de datos de precipitación (ej: en milímetros)
        para el rango de fechas definido, AHORA GENERANDO UN DATO DIARIO.
        """
        print("  > Giovanni: Solicitando datos de Precipitación Diaria Simulada...")
        
        try:
            start_obj = datetime.strptime(self.start_date, '%m%d%Y')
            end_obj = datetime.strptime(self.end_date, '%m%d%Y')
        except ValueError:
            print("❌ Error: Formato de fecha de rango inválido en GiovanniAPI.")
            return []

        # --- LÓGICA CLAVE: Iterar día por día ---
        daily_records = []
        current_date = start_obj
        
        while current_date <= end_obj:
            # Simulamos un valor diario de precipitación (ej: entre 0.0 y 20.0 mm)
            simulated_daily_precip = round(random.uniform(0.0, 20.0), 2)
            
            # El campo EndDate es el que se mapea a MapDate en la base de datos
            record = {
                'EndDate': current_date.strftime('%Y%m%d'), 
                'DailyPrecipitation_mm': simulated_daily_precip,
            }
            daily_records.append(record)
            
            # Avanzamos un día
            current_date += timedelta(days=1)

        print(f"  [Giovanni] ✅ {len(daily_records)} datos diarios simulados generados.")
        
        # Devolvemos la lista de registros diarios
        return daily_records