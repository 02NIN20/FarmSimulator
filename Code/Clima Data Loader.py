import pandas as pd
from datetime import datetime, timedelta
import os
import subprocess 
from typing import Dict, Any, List, Optional

# ====================================================================
# CONFIGURACIÓN DEL SISTEMA
# ====================================================================
# Fecha de inicio REAL para el DÍA 1 del juego (MMDDYYYY)
DEFAULT_START_DATE_STR: str = "01012024"
# Nombre del script de consulta real (Debe estar en el mismo directorio)
AETERNA_SCRIPT: str = "Aeterna_FINAL.py"
# DIRECTORIO DONDE SE ESPERAN LOS ARCHIVOS DE CONSULTA (CSV de salida)
OUTPUT_DIR: str = "output_consultas"
# Lista de ubicaciones a consultar (puedes añadir o quitar aquí)
UBICACIONES_A_CONSULTAR: List[str] = ["CA", "AK", "ND"]


def get_date_from_day(game_day: int) -> str:
    """
    Calcula la fecha real (MMDDYYYY) en función del número de día del juego.
    
    El día 1 del juego (game_day=1) corresponde a la fecha de inicio.
    El día N del juego corresponde a (N - 1) días sumados a la fecha de inicio.
    """
    if game_day < 1:
        # Esto previene errores si el juego inicia en día 0 o negativo, aunque 
        # tu lógica de juego probablemente comience en 1.
        return DEFAULT_START_DATE_STR
        
    try:
        # 1. Convertir la fecha de inicio fija (01012024) a objeto datetime
        start_date = datetime.strptime(DEFAULT_START_DATE_STR, "%m%d%Y")
        
        # 2. Calcular los días a sumar
        days_to_add = game_day - 1
        
        # 3. Calcular la fecha final y formatearla a MMDDYYYY
        target_date = start_date + timedelta(days=days_to_add)
        return target_date.strftime("%m%d%Y")
        
    except ValueError:
        print(f"❌ ERROR: Formato de fecha de inicio '{DEFAULT_START_DATE_STR}' inválido. Usa MMDDYYYY.")
        return DEFAULT_START_DATE_STR


class ConsultaClimaPandas:
    """
    Clase para consultar datos de clima usando pandas. 
    Construye la ruta del archivo y carga los datos.
    """

    def __init__(self, location: str, day_str: str):
        self.location = location.upper()
        self.date_str = day_str
        self.filepath = self._build_filepath() 
        self.df = self._load_data()

    def _build_filepath(self) -> str:
        """ Construye la ruta: output_consultas/CA_01012024_consulta.csv """
        filename = f"{self.location}_{self.date_str}_consulta.csv"
        return os.path.join(OUTPUT_DIR, filename)

    def _load_data(self) -> pd.DataFrame:
        """ Carga el único registro de datos desde el CSV. """
        if not os.path.exists(self.filepath):
            print(f"❌ ERROR: Archivo de datos no encontrado en {self.filepath}.")
            print("         Asegúrate de que Aeterna_FINAL.py se ejecutó correctamente.")
            return pd.DataFrame() 

        try:
            df = pd.read_csv(self.filepath)
            return df
        except Exception as e:
            print(f"❌ Error al leer el archivo CSV con pandas: {e}")
            return pd.DataFrame()

    def get_data_row(self) -> Optional[pd.Series]:
        """ Retorna la fila de datos cargados. """
        if not self.df.empty:
            return self.df.iloc[0]
        return None

    def extract_game_variables(self) -> Optional[Dict[str, Any]]:
        """
        Extrae y normaliza los datos climáticos importantes para la lógica del juego.
        """
        data_row = self.get_data_row()
        if data_row is None:
            return None

        try:
            # Extracción y conversión a tipos nativos de Python
            return {
                'location': self.location,
                'date_mmddyyyy': self.date_str,
                # Usamos .get para asegurar que no falle si la columna falta
                'precipitation_mm': float(data_row.get('Precipitation_mm', 0.0)),
                'ndvi_health': float(data_row.get('NDVI_MODIS', 0.0)),
                'lst_day_temp_k': float(data_row.get('LST_Day_MODIS', 0.0)),
                'wind_speed': float(data_row.get('WindSpeed_GLDAS', 0.0)),
                'soil_moisture': float(data_row.get('SoilMoisture_SMAP', 0.0)),
                # Porcentajes de sequía
                'drought_none_p': float(data_row.get('None_P', 0.0)),
                'drought_d0_p': float(data_row.get('D0_P', 0.0)),
                'drought_d1_p': float(data_row.get('D1_P', 0.0)),
                # Suma de sequía severa/extrema
                'drought_severe_p': float(data_row.get('D2_P', 0.0)) + float(data_row.get('D3_P', 0.0)) + float(data_row.get('D4_P', 0.0)), 
            }
        except Exception as e:
            print(f"❌ Error al procesar datos para {self.location}: {e}")
            return None

def _run_aeterna_query(location: str, date_str: str) -> bool:
    """ Ejecuta el script Aeterna_FINAL.py (python Aeterna_FINAL.py ABRMMDDYYYY) """
    param = f"{location}{date_str}"
    command = ["python", AETERNA_SCRIPT, param]

    print(f"💻 Ejecutando consulta Aeterna: {' '.join(command)}")
    
    try:
        # Ejecutar el comando de forma síncrona
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ Consulta exitosa para {param}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ ERROR CRÍTICO al ejecutar {AETERNA_SCRIPT} para {param}: {e.returncode}")
        print(f"   Error de salida: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"❌ ERROR: Script o Python no encontrado.")
        return False


def load_game_data(game_day: int, game_data_dict: Dict[str, Any]):
    """
    Función principal que usa el día del juego para calcular la fecha real,
    ejecutar Aeterna_FINAL y cargar los datos en el diccionario global del juego.
    """
    
    # 1. Mapear el día de juego al día real (MMDDYYYY)
    fecha_consulta_mmddyyyy = get_date_from_day(game_day)
    
    # 2. Actualizar el estado del diccionario
    game_data_dict['GAME_DAY'] = game_day
    game_data_dict['DATE_TODAY_MMDDYYYY'] = fecha_consulta_mmddyyyy
    
    # 3. Asegurar que el directorio de salida exista
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"📦 Directorio '{OUTPUT_DIR}' creado.")

    print(f"\n--- CARGANDO DATOS (DÍA JUEGO {game_day}) -> FECHA REAL: {fecha_consulta_mmddyyyy} ---")

    # 4. Iterar sobre ubicaciones: CONSULTAR y luego CARGAR
    for ubicacion in UBICACIONES_A_CONSULTAR:
        
        # PASO 4a: Ejecutar Aeterna_FINAL.py para generar el CSV
        success = _run_aeterna_query(ubicacion, fecha_consulta_mmddyyyy)
        
        if not success:
            game_data_dict[ubicacion] = None
            continue

        # PASO 4b: Cargar y procesar el CSV generado
        consulta = ConsultaClimaPandas(ubicacion, fecha_consulta_mmddyyyy)
        data_for_game = consulta.extract_game_variables()
        
        if data_for_game:
            game_data_dict[ubicacion] = data_for_game
            print(f"✅ {ubicacion} OK: Temp_K={data_for_game['lst_day_temp_k']:.1f}, NDVI={data_for_game['ndvi_health']:.2f}")
        else:
            game_data_dict[ubicacion] = None
            print(f"⚠️ {ubicacion} FALLÓ: No se pudieron cargar datos válidos.")

    print("\n--- CARGA DE DATOS FINALIZADA ---\n")

# NOTA: Este módulo NO ejecuta ninguna lógica. Solo exporta funciones.
# La lógica principal se encuentra en el archivo game.py
