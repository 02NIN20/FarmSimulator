class ControladorClima:
    """
    Controlador global que gestiona la transición y viabilidad de los eventos.
    """
    def __init__(self, zona_climatica: int, temp_inicial: float = 25.0):
        
        # --- Condiciones del Mundo (Restricción Geográfica) ---
        self.zona_climatica = zona_climatica # TipoClima.CALIDO, TEMPLADO, FRIO
        self.temperatura = temp_inicial      # Temperatura ambiente (°C)
        self.humedad = random.uniform(40.0, 70.0) # Humedad ambiente (%)
        self.probabilidad_cambio = 0.005     # Probabilidad base de que algo pase por ciclo
        
        # --- Estado del Evento ---
        self.evento_actual: EventoClimaticoBase = Soleado(duracion=180.0)
        self.posibles_eventos = [Soleado, Lluvia, Nieve, TormentaElectrica, Tornado]

    def _es_viable(self, evento_clase, temp: float, humedad: float, zona: int) -> bool:
        """Verifica si un evento es posible dadas las condiciones."""
        
        # Lógica de Restricción Geográfica CLAVE
        if evento_clase is Nieve:
            # 1. Nieve solo en zonas TEMPLADAS o FRIAS
            if zona == TipoClima.CALIDO:
                return False
            # 2. Nieve solo si la temperatura es lo suficientemente baja
            return temp <= 2.0

        if evento_clase is TormentaElectrica:
            # Requiere inestabilidad: alta humedad y temperatura moderada/alta
            return humedad > 75.0 and temp >= 15.0

        if evento_clase is Tornado:
            # Requiere zonas TEMPLADAS (Choque de masas de aire) y alta inestabilidad
            return zona == TipoClima.TEMPLADO and temp >= 20.0 and humedad > 60.0

        if evento_clase is Lluvia:
            # La lluvia es posible con humedad moderada
            return humedad > 40.0
            
        return True # Soleado siempre es viable

    def _elegir_proximo_evento(self):
        """Selecciona y crea un nuevo evento viable."""
        
        eventos_candidatos = []
        for evento_clase in self.posibles_eventos:
            if self._es_viable(evento_clase, self.temperatura, self.humedad, self.zona_climatica):
                eventos_candidatos.append(evento_clase)

        # Si el evento actual es la única opción, mantenlo
        if len(eventos_candidatos) == 1 and eventos_candidatos[0].__name__ == self.evento_actual.nombre:
             return
             
        # Elegir un nuevo evento al azar (con más peso para Soleado si está disponible)
        if Soleado in eventos_candidatos:
             # Duplicar Soleado para aumentar su probabilidad
             eventos_candidatos.append(Soleado)
             
        nueva_clase = random.choice(eventos_candidatos)

        # Crear una nueva instancia del evento
        intensidad = random.uniform(0.3, 1.0)
        duracion = random.uniform(60.0, 300.0)
        
        # Aquí se instancia el evento con sus parámetros
        if nueva_clase is Soleado:
            self.evento_actual = Soleado(duracion)
        elif nueva_clase is Lluvia:
            self.evento_actual = Lluvia(intensidad, duracion)
        elif nueva_clase is Nieve:
            self.evento_actual = Nieve(intensidad, duracion)
        elif nueva_clase is Tornado:
            # Los tornados son raros y deben ser muy intensos
            self.evento_actual = Tornado(random.uniform(0.8, 1.0), random.uniform(30.0, 120.0))
        # ... otros eventos

    def update(self, delta_time: float):
        """Actualiza las condiciones ambientales y el evento actual."""
        
        # 1. Simulación de Condiciones Ambientales (Fluctuación)
        if self.zona_climatica == TipoClima.TEMPLADO:
            # La temperatura fluctúa ligeramente con el tiempo (simulación de día/noche)
            self.temperatura += math.sin(get_time() * 0.001) * 0.05 * delta_time 
            self.temperatura = max(-10.0, min(40.0, self.temperatura)) # Limitar rango

        # 2. Actualizar Evento Actual
        self.evento_actual.update(delta_time, self.temperatura, self.humedad)
        
        # 3. Lógica de Transición de Evento
        probabilidad = self.probabilidad_cambio # Probabilidad de cambio por ciclo
        
        if not self.evento_actual.esta_activo:
            probabilidad = 1.0 # Forzar cambio si el evento terminó
            
        if random.random() < probabilidad:
            self._elegir_proximo_evento()

    def draw(self, ancho_mundo: int, alto_mundo: int):
        """Dibuja el evento y muestra la información de debug."""
        
        self.evento_actual.draw(ancho_mundo, alto_mundo)
        
        # Info de Debug
        draw_text(f"Zona: {self.zona_climatica} | Evento: {self.evento_actual.nombre}", 10, 10, 20, BLACK)
        draw_text(f"Temp: {self.temperatura:.1f}°C | Humedad: {self.humedad:.0f}%", 10, 35, 20, BLACK)