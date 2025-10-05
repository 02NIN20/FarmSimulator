import subprocess
import datetime

# --- Configuración ---
# Estados (ABR) a consultar según tu requisito
ESTADOS_A_CONSULTAR = ["CA", "AK", "ND"]
# Nombre del script principal de la NASA
SCRIPT_AETERNA = "Aeterna_FINAL.py"

def ejecutar_consulta_aeterna(abreviatura: str, fecha_obj: datetime.date):
    """
    Simula la ejecución del comando de Consulta Específica (2.2) de Aeterna_FINAL.py.
    
    El formato de la fecha es MMDDYYYY.
    El comando completo es: python Aeterna_FINAL.py ABRMMDDYYYY
    """
    # Formato de fecha MMDDYYYY (Mes-Día-Año)
    fecha_formato = fecha_obj.strftime("%m%d%Y")
    
    # Construcción del parámetro ABRMMDDYYYY
    parametro_completo = abreviatura + fecha_formato
    
    # Comando completo a "ejecutar"
    comando = ["python", SCRIPT_AETERNA, parametro_completo]
    
    print(f"--- Ejecutando para {abreviatura} en {fecha_obj.isoformat()} ({parametro_completo}) ---")
    
    try:
        print(f"Comando REAL a ejecutar: {' '.join(comando)}")

        # ----------------------------------------------------
        # ESTE ES EL CAMBIO CLAVE: Ejecuta el script de la NASA
        # ----------------------------------------------------
        resultado = subprocess.run(comando, check=True, capture_output=True, text=True, cwd=".")
        
        # Opcional: Mostrar la salida del script real
        print(f"Aeterna_FINAL.py (STDOUT):\n{resultado.stdout}")
        print(f"Consulta para {abreviatura} en {fecha_obj.isoformat()} completada. El CSV debe haberse generado.")
        
    except subprocess.CalledProcessError as e:
        # Manejo de error si el script Aeterna_FINAL.py falla
        print(f"ERROR: Aeterna_FINAL.py falló con código de retorno {e.returncode}.")
        print(f"Salida de Error (STDERR):\n{e.stderr}")
    except FileNotFoundError:
        # Manejo de error si el ejecutable 'python' o el script no se encuentra
        print(f"ERROR FATAL: El archivo '{SCRIPT_AETERNA}' o 'python' no fue encontrado.")
def main():
    """
    Función principal para iterar a través de los días y estados.
    """
    # --- Variables de control configurables ---
    # Fija la fecha de inicio. Formato: YYYY-MM-DD
    fecha_inicio_str = input("Ingrese la fecha de inicio (YYYY-MM-DD, ej: 2024-06-15): ")
    try:
        fecha_actual = datetime.datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
    except ValueError:
        print("Formato de fecha inválido. Usando fecha por defecto: 2024-06-15.")
        fecha_actual = datetime.date(2024, 6, 15)
        
    # Fija el número de días que se consultará dinámicamente
    try:
        dias_a_iterar = int(input("Ingrese el número de días a consultar (ej: 5): "))
    except ValueError:
        print("Número de días inválido. Usando por defecto: 5 días.")
        dias_a_iterar = 5
        
    # Variable que representa el "DAY" que cambia externamente
    for day in range(dias_a_iterar):
        print("\n" + "="*50)
        print(f"*** DÍA DE CONSULTA DINÁMICA: {day + 1} / {dias_a_iterar} - FECHA: {fecha_actual.isoformat()} ***")
        print("="*50)

        # Itera sobre cada estado (ABR)
        for estado in ESTADOS_A_CONSULTAR:
            ejecutar_consulta_aeterna(estado, fecha_actual)

        # AVANZA AL DÍA SIGUIENTE (Variable 'DAY' incrementa su valor de día)
        # Esto hace que la consulta MMDDYYYY cambie al día siguiente.
        fecha_actual += datetime.timedelta(days=1)
        
    print("\n" + "="*50)
    print("Proceso de consulta dinámica finalizado.")
    print("Recuerda que Aeterna_FINAL.py exporta el resultado a un archivo CSV (Manual 2.2).")

if __name__ == "__main__":
    main()