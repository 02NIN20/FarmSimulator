# core/database_manager.py

class DatabaseManager:
    """Clase base para futuras extensiones de manejo de DB si fuera necesario."""
    
    def __init__(self, db_file):
        self.db_file = db_file
        
    def get_connection(self):
        # La conexi�n real se manejar� en CropZone por simplicidad.
        return None