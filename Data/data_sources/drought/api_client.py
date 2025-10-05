# data_sources/drought/api_client.py
# -*- coding: utf-8 -*-
import requests
import csv
from io import StringIO
import re
from datetime import datetime, timedelta

class DroughtAPI:
    """Clase para interactuar con la API real del U.S. Drought Monitor."""
    
    BASE_URL = "https://usdmdataservices.unl.edu/api/{}/GetDroughtSeverityStatisticsByAreaPercent"

    def __init__(self, area_type, aoi_code, state_abbr, start_date, end_date):
        self.area_type = area_type
        self.aoi_code = aoi_code
        self.state_abbr = state_abbr # Almacenamos el state_abbr
        self.start_date = start_date
        self.end_date = end_date
        
        # Cabeceras Esperadas (Solo las que nos interesan)
        self.expected_headers = [
            'MapDate', 'StateAbbreviation', 'None', 'D0', 'D1', 'D2', 'D3', 'D4'
        ]

    def _to_float_safe(self, value):
        """Convierte un valor a float. Devuelve 0.0 si es None o vacío, para asegurar la suma total."""
        if value is None or str(value).strip() == '':
            return 0.0
        try:
            return float(value)
        except ValueError:
            return 0.0

    def fetch_data(self):
        """Obtiene datos de sequía en formato tabular (CSV)."""
        
        url = self.BASE_URL.format(self.area_type)
        
        # ⚠️ Necesitamos convertir las fechas MMDDYYYY a M/D/YYYY para la API
        try:
            start_obj = datetime.strptime(self.start_date, '%m%d%Y') - timedelta(days=7) # Retrocedemos 7 días
            end_obj = datetime.strptime(self.end_date, '%m%d%Y')
            start_date_api = start_obj.strftime('%#m/%#d/%Y')
            end_date_api = end_obj.strftime('%#m/%#d/%Y')
        except ValueError:
            print("❌ Error: Formato de fecha inválido. Usar MMDDYYYY.")
            return []

        parametros = {
            'aoi': self.aoi_code,
            'startdate': start_date_api,
            'enddate': end_date_api,
            'statisticsType': 1 # Formato tradicional (D0-D4)
        }

        try:
            response = requests.get(url, params=parametros)
            response.raise_for_status()

            csv_data = StringIO(response.text)
            lector_csv = csv.reader(csv_data)
            
            datos_sequia = []
            cabeceras = []
            indices = {}
            
            for i, fila in enumerate(lector_csv):
                # 1. PROCESAMIENTO DE CABECERAS
                if i == 0:
                    # Limpiamos las cabeceras
                    cabeceras = [re.sub(r'[^a-zA-Z0-9_]', '', h.strip()) for h in fila]
                    
                    # Mapear los índices de las cabeceras esperadas a su posición real
                    for header in self.expected_headers:
                        if header in cabeceras:
                            indices[header] = cabeceras.index(header)
                    
                    # Verificación CRÍTICA: Solo necesitamos los porcentajes y MapDate
                    critical_headers = ['MapDate', 'None', 'D0', 'D1', 'D2', 'D3', 'D4']
                    if not all(h in indices for h in critical_headers):
                        print(f"⚠️ Alerta: Faltan cabeceras de sequía críticas. Sólo se encontraron {list(indices.keys())}")
                        return [] # Fallo si faltan los datos principales
                        
                    continue
                
                # 2. EXTRACCIÓN CON FALLBACK (para StateAbbreviation)
                if not fila or not fila[0]:
                    continue # Salta filas vacías o sin fecha

                # Fallback para StateAbbreviation: si no encontramos la columna, usamos el valor de la instancia.
                if 'StateAbbreviation' in indices:
                    state_abbr_value = fila[indices['StateAbbreviation']]
                else:
                    state_abbr_value = self.state_abbr
                    
                # Creamos una tupla de datos siguiendo el orden lógico que espera zone_model.py
                # Orden: MapDate, StateAbbreviation, None, D0, D1, D2, D3, D4
                try:
                    data_tuple = (
                        fila[indices['MapDate']],
                        state_abbr_value,
                        self._to_float_safe(fila[indices['None']]),
                        self._to_float_safe(fila[indices['D0']]),
                        self._to_float_safe(fila[indices['D1']]),
                        self._to_float_safe(fila[indices['D2']]),
                        self._to_float_safe(fila[indices['D3']]),
                        self._to_float_safe(fila[indices['D4']])
                    )
                    datos_sequia.append(list(data_tuple))
                    
                except IndexError as e:
                    print(f"❌ Error en el procesamiento de la fila: Índice faltante ({e}). Fila omitida.")
                    continue
            
            return datos_sequia

        except requests.exceptions.RequestException as e:
            print(f"❌ Error al obtener los datos de la API (HTTP/Conexión): {e}")
            return []
        except Exception as e:
            print(f"❌ Ocurrió un error inesperado al procesar los datos: {e}")
            return []