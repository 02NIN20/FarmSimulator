# data_sources/appeears/appeears_api.py
# -*- coding: utf-8 -*-
import random
from datetime import datetime

class AppEEARSAPI:
    """Clase para simular la interacción con la API de AppEEARS (Datos Satelitales Diarios)."""
    
    # Simulación de la URL base
    BASE_URL = "https://appeears.earthdatacloud.nasa.gov/api/task"
    
    def __init__(self, fips_code, target_date):
        # Para AppEEARS, usaremos el FIPS code para identificar la zona.
        self.fips_code = fips_code
        self.target_date = target_date # MMDDYYYY
        print(f"  [AppEEARSAPI] Inicializada para FIPS {fips_code} y fecha {target_date}.")

    def fetch_daily_data(self):
        """
        Simula la obtención de un solo registro de datos satelitales (un punto en el tiempo).
        """
        # La API real de AppEEARS es compleja y lenta. Aquí simulamos el dato.
        
        try:
            target_obj = datetime.strptime(self.target_date, '%m%d%Y')
        except ValueError:
            print("❌ Error: Formato de fecha objetivo inválido en AppEEARSAPI.")
            return []
            
        print(f"  > AppEEARS: Solicitando datos satelitales para {self.target_date}...")

        # Simulación de valores
        simulated_record = {
            'MapDate': target_obj.strftime('%Y%m%d'), # Usamos el formato DB (YYYYMMDD)
            
            # Humedad del Suelo (ej. 0 a 1)
            'SoilMoisture_SMAP': round(random.uniform(0.1, 0.9), 4),
            
            # Vigor de Vegetación (NDVI) (ej. -1 a 1)
            'NDVI_MODIS': round(random.uniform(0.1, 0.8), 4),
            
            # Temperatura de la Superficie Terrestre (LST) Diurna (ej. Kelvin)
            'LST_Day_MODIS': round(random.uniform(280.0, 320.0), 2),
            
            # Velocidad del Viento (ej. m/s)
            'WindSpeed_GLDAS': round(random.uniform(1.0, 10.0), 2),
        }
        
        print(f"  [AppEEARS] ✅ Dato simulado generado para {self.target_date}.")
        
        # Devolvemos el dato en una lista para mantener consistencia
        return [simulated_record] 

# Asegúrate de crear un archivo `__init__.py` vacío en el directorio `appeears` si no existe.