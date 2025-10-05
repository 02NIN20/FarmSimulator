# data_sources/drought/zone_model.py (CÓDIGO CORREGIDO)
# -*- coding: utf-8 -*-
import json
import sqlite3
from datetime import datetime, timedelta

# 🎯 IMPORTACIONES DESDE LOS MÓDULOS SEPARADOS (AHORA IMPLEMENTADOS)
from data_sources.drought.api_client import DroughtAPI     # Sequía
from data_sources.giovanni.giovanni_api import GiovanniAPI # <<<< NUEVA IMPORTACIÓN
from data_sources.appeears.appeears_api import AppEEARSAPI # <<<< NUEVA IMPORTACIÓN

DB_FILE = 'sequia.db'

# ==============================================================================
# FUNCIÓN AUXILIAR (CORRECTA Y NECESARIA)
# ==============================================================================
def _to_float_or_none(value):
    """Convierte un valor a float. Si es None, vacío, o no se puede convertir, devuelve None."""
    if value is None or str(value).strip() == '':
        return None
    try:
        return float(value)
    except ValueError:
        return None  

# ==============================================================================
# CLASE AUXILIAR: JSONFormatter
# ==============================================================================
class JSONFormatter:
    """
    Clase auxiliar responsable de tomar datos de la base de datos y formatearlos como JSON.
    """
    def __init__(self, column_names):
        self.column_names = column_names

    def format_to_list(self, records):
        # Asumimos que row_factory ya devuelve diccionarios, pero esta función maneja tuplas si es necesario.
        return [dict(row) for row in records] if records and isinstance(records[0], sqlite3.Row) else records

    def get_json_string(self, data_list):
        return json.dumps(data_list, indent=4)


# ==============================================================================
# CLASE PRINCIPAL: CropZone
# ==============================================================================
class CropZone:
    """
    Orquesta los datos de Sequía, Precipitación, Humedad, Vigor, Temp y Vientos.
    """
    # Columnas de la tabla
    DB_COLUMNS = [
        'MapDate', 'StateAbbreviation', 'FipsCode', 
        'None_P', 'D0_P', 'D1_P', 'D2_P', 'D3_P', 'D4_P', # Sequía
        'Precipitation_mm',                                  # <<<< CORRECCIÓN 1: Nuevo nombre de columna
        'SoilMoisture_SMAP', 'NDVI_MODIS', 'LST_Day_MODIS', 'WindSpeed_GLDAS' # AppEEARS
    ]

    def __init__(self, name, state_abbr, fips_code):
        self.name = name
        self.state_abbr = state_abbr
        self.fips_code = fips_code
        self._ensure_db_and_table()

    # --------------------------------------------------------------------------
    # LÓGICA DE BASE DE DATOS (CREATE/ALTER)
    # --------------------------------------------------------------------------
    def _ensure_db_and_table(self):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # 1. Creación de la tabla con todas las columnas
        # <<<< CORRECCIÓN 2: Usar 'Precipitation_mm' en la creación de la tabla
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS sequia_data (
                MapDate TEXT NOT NULL,
                StateAbbreviation TEXT NOT NULL,
                FipsCode TEXT NOT NULL,
                None_P REAL, D0_P REAL, D1_P REAL, D2_P REAL, D3_P REAL, D4_P REAL,
                Precipitation_mm REAL,
                SoilMoisture_SMAP REAL, NDVI_MODIS REAL, LST_Day_MODIS REAL, WindSpeed_GLDAS REAL,
                PRIMARY KEY (MapDate, FipsCode)
            )
        """)

        # 2. ALTER TABLE para asegurar que existan las nuevas columnas
        # <<<< CORRECCIÓN 3: Asegurar que la nueva columna exista
        new_columns = ['Precipitation_mm', 'SoilMoisture_SMAP', 'NDVI_MODIS', 'LST_Day_MODIS', 'WindSpeed_GLDAS']
        for col in new_columns:
            try:
                cursor.execute(f"ALTER TABLE sequia_data ADD COLUMN {col} REAL")
            except sqlite3.OperationalError:
                pass
            
        conn.commit()
        conn.close()
        print(f"✅ Estructura de tabla 'sequia_data' verificada/creada para {self.name}.")
    
    # --------------------------------------------------------------------------
    # MODO ACTUALIZACIÓN: ORQUESTADOR DE RANGO DE FECHAS (FULL)
    # --------------------------------------------------------------------------
    def run_full_range_update(self, start_date, end_date):
        """
        Orquesta la actualización de TODAS las fuentes de datos (Sequía, Giovanni, AppEEARS)
        en el rango de fechas especificado.
        """
        print(f"\n--- INICIANDO ACTUALIZACIÓN para {self.name} ({self.state_abbr}) ---")

        # 1. ACTUALIZACIÓN DE SEQUÍA (USDN) Y PRECIPITACIÓN (GIOVANNI)
        print(f"  > Sequía y Precipitación: Buscando datos entre {start_date} y {end_date}...")
        self.run_drought_update(start_date, end_date)
        self.run_giovanni_update(start_date, end_date) # <<<< LLAMADA IMPLEMENTADA

        # 2. ACTUALIZACIÓN DE DATOS SATELITALES (APPEEARS)
        print(f"  > AppEEARS: Iniciando actualización diaria...")
        
        try:
            current_date_dt = datetime.strptime(start_date, '%m%d%Y')
            end_date_dt = datetime.strptime(end_date, '%m%d%Y')
        except ValueError:
            print("❌ Error: Formato de fecha de rango inválido. Asegúrese de usar MMDDYYYY.")
            return

        total_updated_days = 0
        while current_date_dt <= end_date_dt:
            date_str = current_date_dt.strftime('%m%d%Y')
            
            # Llama al método de actualización de AppEEARS para la fecha actual
            self.run_appeears_update(date_str) # <<<< LLAMADA IMPLEMENTADA
            
            current_date_dt += timedelta(days=1)
            total_updated_days += 1
            
        print(f"\n✅ FINALIZADO: Actualización de rango para {self.name} completada. Días iterados: {total_updated_days}.")

    # --------------------------------------------------------------------------
    # MÉTODOS DE ESCRITURA/ACTUALIZACIÓN (_save_data)
    # --------------------------------------------------------------------------
    def _save_data(self, data, update_type):
        """Método centralizado para guardar datos (INSERT OR IGNORE + UPDATE)."""
        if not data: return 0
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        inserted_count = 0
        
        # =====================================================================
        # Lógica de Sequía (APLICACIÓN DE LA LÓGICA EXCLUSIVA)
        # =====================================================================
        if update_type == 'drought':
            
            db_data = []
            # item es una lista de 8 elementos: [MapDate, StateAbbreviation, None, D0, D1, D2, D3, D4]
            for item in data:
                # La API de Drought Monitor devuelve MapDate en formato YYYYMMDD
                map_date_db = item[0] 
                
                # Convertir los valores a float de forma segura
                NONE_CUM = _to_float_or_none(item[2])
                D0_CUM = _to_float_or_none(item[3]) # Porcentaje en D0 o peor
                D1_CUM = _to_float_or_none(item[4]) 
                D2_CUM = _to_float_or_none(item[5]) 
                D3_CUM = _to_float_or_none(item[6]) 
                D4_CUM = _to_float_or_none(item[7]) 
                
                # --- CÁLCULO DE PORCENTAJES EXCLUSIVOS ---
                D4_P_EXC = D4_CUM if D4_CUM is not None else 0.0
                D3_P_EXC = (D3_CUM - D4_CUM) if D3_CUM is not None and D4_CUM is not None else 0.0
                D2_P_EXC = (D2_CUM - D3_CUM) if D2_CUM is not None and D3_CUM is not None else 0.0
                D1_P_EXC = (D1_CUM - D2_CUM) if D1_CUM is not None and D2_CUM is not None else 0.0
                D0_P_EXC = (D0_CUM - D1_CUM) if D0_CUM is not None and D1_CUM is not None else 0.0
                NONE_P_EXC = NONE_CUM if NONE_CUM is not None else 0.0
                # ----------------------------------------

                # Prepara la tupla de 8 elementos para el UPDATE (6 valores exclusivos + MapDate + FipsCode)
                db_data.append((
                    NONE_P_EXC, D0_P_EXC, D1_P_EXC, D2_P_EXC, D3_P_EXC, D4_P_EXC,
                    map_date_db, self.fips_code
                ))
            
            # 1. Aseguramos que la fila exista (INSERT OR IGNORE)
            # El item[1] es StateAbbreviation (usado para completar la fila)
            sql_insert = "INSERT OR IGNORE INTO sequia_data (MapDate, StateAbbreviation, FipsCode) VALUES (?, ?, ?)"
            insert_data = [(d[6], item[1], d[7]) for d, item in zip(db_data, data)]
            cursor.executemany(sql_insert, insert_data)

            # 2. Actualizamos las columnas de sequía (UPDATE)
            sql_update = """
                UPDATE sequia_data SET 
                    None_P = ?, D0_P = ?, D1_P = ?, D2_P = ?, D3_P = ?, D4_P = ?
                WHERE MapDate = ? AND FipsCode = ?
            """
            cursor.executemany(sql_update, db_data)
            inserted_count = cursor.rowcount
            
        # =====================================================================
        # Lógica de Precipitación (giovanni) y Satélite (appeears)
        # =====================================================================
        elif update_type == 'giovanni':
            # <<<< CORRECCIÓN 4: Bucle para manejar múltiples registros diarios
            
                for record in data:
                    # 1. INTENTA INSERTAR la fila (si no existe)
                    sql_insert = "INSERT OR IGNORE INTO sequia_data (MapDate, StateAbbreviation, FipsCode) VALUES (?, ?, ?)"
                    # Usa 'EndDate' del registro de Giovanni como MapDate en la DB
                    cursor.execute(sql_insert, (record['EndDate'], self.state_abbr, self.fips_code)) 
        
                    # 2. ACTUALIZA la columna de Precipitación
                    sql_update = "UPDATE sequia_data SET Precipitation_mm = ? WHERE MapDate = ? AND FipsCode = ?"
                    cursor.execute(sql_update, (record['DailyPrecipitation_mm'], record['EndDate'], self.fips_code))
                    inserted_count += cursor.rowcount
            
        elif update_type == 'appeears':
            record = data[0]
            sql_insert = "INSERT OR IGNORE INTO sequia_data (MapDate, StateAbbreviation, FipsCode) VALUES (?, ?, ?)"
            # Usa 'MapDate' del registro de AppEEARS
            cursor.execute(sql_insert, (record['MapDate'], self.state_abbr, self.fips_code)) 
            sql_update = """
                UPDATE sequia_data 
                SET SoilMoisture_SMAP = ?, NDVI_MODIS = ?, LST_Day_MODIS = ?, WindSpeed_GLDAS = ?
                WHERE MapDate = ? AND FipsCode = ?
            """
            cursor.execute(sql_update, (
                record['SoilMoisture_SMAP'], record['NDVI_MODIS'], 
                record['LST_Day_MODIS'], record['WindSpeed_GLDAS'], 
                record['MapDate'], self.fips_code
            ))
            inserted_count = cursor.rowcount
            
        try:
            conn.commit()
            return inserted_count
        finally:
            conn.close()

    # --------------------------------------------------------------------------
    # MÉTODOS DE ACTUALIZACIÓN (run_drought_update, run_giovanni_update, run_appeears_update)
    # --------------------------------------------------------------------------
    def run_drought_update(self, start_date, end_date):
        """
        Orquesta la obtención de datos de Sequía (USDN) para el rango y los guarda en la DB.
        """
        print(f"  > Sequía: Buscando datos entre {start_date} y {end_date}...")

        # 1. Llamar a la API para obtener el rango de datos
        api_client = DroughtAPI(
            area_type='StateStatistics', 
            aoi_code=self.fips_code,     # CORRECCIÓN: USAR FIPS_CODE
            state_abbr=self.state_abbr,  
            start_date=start_date, 
            end_date=end_date
        )
        
        drought_records = api_client.fetch_data() 
        
        # 2. Guardar los datos obtenidos
        if drought_records:
            count = self._save_data(drought_records, 'drought')
            # La API de Drought Monitor devuelve semanalmente (aprox. 52 filas por año)
            print(f"  [DB] ✅ Registros de sequía guardados/actualizados: {count} filas.")
        else:
            print(f"  [DB] ⚠️ No se obtuvieron datos de sequía de la API para {self.name}.")
            
    def run_giovanni_update(self, start_date, end_date): # <<<< IMPLEMENTADO
        """
        Orquesta la obtención de datos de Precipitación (Giovanni) para el rango y los guarda en la DB.
        """
        # 1. Llamar a la API para obtener el rango de datos (Precipitación acumulada)
        api_client = GiovanniAPI(
            fips_code=self.fips_code, 
            start_date=start_date, 
            end_date=end_date
        )
        precip_records = api_client.fetch_range_data()
        
        # 2. Guardar los datos obtenidos
        if precip_records:
            # <<<< La simulación ahora devuelve múltiples registros, ajustamos el mensaje:
            count = self._save_data(precip_records, 'giovanni')
            print(f"  [DB] ✅ Registros de precipitación guardados/actualizados: {count} filas.") 
        else:
            print(f"  [DB] ⚠️ No se obtuvieron datos de precipitación de la API para {self.name}.")
            
    def run_appeears_update(self, date_to_update): # <<<< IMPLEMENTADO
        """
        Orquesta la obtención de datos Satelitales (AppEEARS) para un solo día y los guarda en la DB.
        """
        # 1. Llamar a la API para obtener el dato diario
        api_client = AppEEARSAPI(
            fips_code=self.fips_code, 
            target_date=date_to_update
        )
        appeears_records = api_client.fetch_daily_data()
        
        # 2. Guardar los datos obtenidos
        if appeears_records:
            count = self._save_data(appeears_records, 'appeears')
            # La API simulada de AppEEARS devuelve 1 fila por día
            print(f"  [DB] ✅ Registros satelitales guardados/actualizados: {count} filas.") 
        else:
            print(f"  [DB] ⚠️ No se obtuvieron datos satelitales de la API para {self.name} el día {date_to_update}.")

    # --------------------------------------------------------------------------
    # FUNCIÓN AUXILIAR SQL para Proximidad (NECESARIA PARA LA BÚSQUEDA AVANZADA)
    # --------------------------------------------------------------------------
    def _get_proximity_subquery(self, target_date_sql, fips_code, columns, alias, min_criteria_col):
        """Genera una subconsulta para encontrar el registro más cercano a una fecha
        que cumpla con un criterio mínimo (columna no nula)."""
        
        # Convierte la columna MapDate (YYYYMMDD) a fecha para cálculo de proximidad
        date_col_sql = "substr(MapDate, 1, 4) || '-' || substr(MapDate, 5, 2) || '-' || substr(MapDate, 7, 2)"
        
        # Calcula la diferencia absoluta en días
        proximity_sql = f"ABS(julianday({date_col_sql}) - julianday('{target_date_sql}'))"
        
        # La subconsulta selecciona todas las columnas necesarias, ordenada por proximidad.
        query = f"""
            (
                SELECT MapDate AS {alias}_MapDate, {columns}
                FROM sequia_data
                WHERE FipsCode = '{fips_code}' AND {min_criteria_col} IS NOT NULL
                ORDER BY {proximity_sql}
                LIMIT 1
            ) AS {alias}
        """
        return query

    # --------------------------------------------------------------------------
    # MÉTODOS DE CONSULTA (Consulta avanzada) 
    # --------------------------------------------------------------------------
    def get_consolidated_by_proximity(self, target_date):
        """
        Busca el registro más cercano a la fecha objetivo para cada categoría (sequía, 
        precipitación, satélite) y los consolida en un solo JSON.
        """
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 1. Convertir la fecha objetivo a formato SQL para el cálculo (YYYY-MM-DD)
            target_date_sql = datetime.strptime(target_date, '%m%d%Y').strftime('%Y-%m-%d')
            
            # --- DEFINICIÓN DE SUBCONSULTAS POR CATEGORÍA ---
            
            # 1. Sequía (Drought Monitor - DM): Usa None_P como criterio
            drought_cols = "None_P, D0_P, D1_P, D2_P, D3_P, D4_P"
            sq_drought = self._get_proximity_subquery(target_date_sql, self.fips_code, drought_cols, 'DM', 'None_P')
            
            # 2. Precipitación (Giovanni - GIO): Usa Precipitation_mm como criterio
            # <<<< CORRECCIÓN 6: Usar el nuevo nombre de columna en la consulta
            precip_cols = "Precipitation_mm"
            sq_precip = self._get_proximity_subquery(target_date_sql, self.fips_code, precip_cols, 'GIO', 'Precipitation_mm')
            
            # 3. Satélite/Humedad (AppEEARS - APP): Usa SoilMoisture_SMAP como criterio
            appeears_cols = "SoilMoisture_SMAP, NDVI_MODIS, LST_Day_MODIS, WindSpeed_GLDAS"
            sq_appeears = self._get_proximity_subquery(target_date_sql, self.fips_code, appeears_cols, 'APP', 'SoilMoisture_SMAP')
            
            # --- CONSULTA FINAL (JOIN de los resultados) ---
            query = f"""
                SELECT
                    '{target_date}' AS TargetDate,
                    DM.DM_MapDate AS DroughtDate,
                    DM.None_P, DM.D0_P, DM.D1_P, DM.D2_P, DM.D3_P, DM.D4_P,
                    
                    GIO.GIO_MapDate AS PrecipDate,
                    GIO.Precipitation_mm,
                    
                    APP.APP_MapDate AS SatelliteDate,
                    APP.SoilMoisture_SMAP, APP.NDVI_MODIS, APP.LST_Day_MODIS, APP.WindSpeed_GLDAS
                FROM 
                    {sq_drought}, 
                    {sq_precip},
                    {sq_appeears};
            """

            cursor.execute(query)
            
            records = [dict(row) for row in cursor.fetchall()]
            
            conn.close()

            if not records or records[0]['DroughtDate'] is None:
                return json.dumps({ "error": f"No se encontró información consolidada para el FipsCode {self.fips_code} cerca de la fecha {target_date}." })
            
            # Devolver el único registro consolidado
            return json.dumps(records, indent=4)

        except ValueError:
            return json.dumps({ "error": "Formato de fecha de consulta inválido. Por favor, use 'MMDDYYYY'." })
        except Exception as e:
            return json.dumps({ "error": f"Error al realizar la consulta de proximidad por categoría: {e}" })
            
    # El método get_data_by_date_range es la consulta de rango antigua
    def get_data_by_date_range(self, start_date, end_date):
        """
        Consulta todos los datos consolidados en un rango de fechas específico.
        """
        try:
            conn = sqlite3.connect(DB_FILE)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            start_dt_db = datetime.strptime(start_date, '%m%d%Y').strftime('%Y%m%d') if start_date else None
            end_dt_db = datetime.strptime(end_date, '%m%d%Y').strftime('%Y%m%d') if end_date else None
            
            # Consulta SQL para seleccionar todos los datos consolidados
            sql = f"""
                SELECT 
                    MapDate, StateAbbreviation, FipsCode, 
                    None_P, D0_P, D1_P, D2_P, D3_P, D4_P,
                    Precipitation_mm,
                    SoilMoisture_SMAP, NDVI_MODIS, LST_Day_MODIS, WindSpeed_GLDAS
                FROM sequia_data 
                WHERE FipsCode = ?
            """
            params = [self.fips_code]

            if start_dt_db:
                sql += " AND MapDate >= ?"
                params.append(start_dt_db)
            if end_dt_db:
                sql += " AND MapDate <= ?"
                params.append(end_dt_db)
            
            sql += " ORDER BY MapDate"

            cursor.execute(sql, tuple(params))
            records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            if not records:
                return json.dumps({ "error": f"No hay datos para {self.name} en el rango solicitado." })
            
            # Formatear y devolver JSON
            return json.dumps(records, indent=4)
            
        except ValueError:
            return json.dumps({ "error": "Formato de fecha inválido. Por favor, use 'MMDDYYYY'." })
        except Exception as e:
            return json.dumps({ "error": f"Error al consultar el rango de datos: {e}" })