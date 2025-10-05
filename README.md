ASTRA: NASA Space Apps Challenge
🚀 Visión General del Proyecto
ASTRA es un juego de simulación agrícola desarrollado en Python (usando la librería Pyray/Raylib) para el NASA Space Apps Challenge.

Este proyecto se enfoca en integrar datos climáticos y ambientales reales obtenidos mediante la simulación de la herramienta Aeterna para influir directamente en la jugabilidad. El objetivo es que el jugador gestione una granja en un entorno dinámico donde las condiciones de cultivo y el éxito de la granja dependen de los datos de precipitación, humedad, temperatura y salud de la vegetación (NDVI).

⚙️ Estructura del Sistema
El juego ASTRA se compone de varios módulos que separan la lógica del motor, el tiempo y la simulación externa:

main.py & game.py: El motor principal del juego. game.py orquesta todos los sistemas (jugador, inventario, crafting y managers) y maneja el bucle de juego. También controla los estados principales (Menú Principal, Configuración, Jugar).

game_clock.py: Gestiona el tiempo interno. Controla el día, la hora y la estación del juego, basándose en 300 segundos (5 minutos) de tiempo real por cada día de juego.

Clima Data Loader.py: El puente de la simulación. Se encarga de mapear el día del juego a una fecha real, ejecutar el script externo Aeterna_FINAL.py para consultar datos climáticos y luego cargar esos resultados al motor del juego.

game_config.py: Define constantes globales como las resoluciones de pantalla disponibles.

🛠️ Cómo Iniciar el Juego y la Simulación
Para ejecutar ASTRA, es crucial que el sistema de consulta de datos externos funcione correctamente, ya que el juego depende de los archivos CSV generados.

1. Requisitos Previos
Necesitarás tener instalado:

Python 3.x

Pyray (Raylib), la librería gráfica.

Pandas, necesario para el script Clima Data Loader.py.

El script Aeterna_FINAL.py (debe estar en el mismo directorio que el resto de archivos).

Instala las dependencias principales (asumiendo que Pyray ya está configurado):

Bash

pip install pandas
2. Ejecución
El juego comienza la simulación el día 1, que se mapea a la fecha real 01/01/2024.

Para que ASTRA funcione, primero debe crear el directorio de salida y los archivos CSV iniciales:

Crea el Directorio de Salida:

Bash

mkdir output_consultas
Ejecuta el Juego:
El script main.py inicializará el motor, que a su vez intentará ejecutar Aeterna_FINAL.py para las ubicaciones predefinidas (CA, AK, ND) al avanzar el día de juego.

Bash

python main.py
3. Solución de Problemas con Datos
Si encuentras el error ❌ ERROR: Script o Python no encontrado al ejecutar, asegúrate de que el archivo Aeterna_FINAL.py se encuentre en el directorio raíz del proyecto y que las dependencias de Pandas estén instaladas.

🎮 Controles Básicos (En el Estado PLAY)
W/A/S/D: Movimiento del personaje.

ESC: Abrir el menú de pausa y opciones.

ENTER: Seleccionar un ítem en el menú principal.

I/TAB: Abrir el inventario (asumiendo el estándar de un juego de simulación).