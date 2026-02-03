"""
Módulo de conexión con Supabase.
Provee la instancia del cliente y utilidades de base de datos.
"""
import os
from supabase import create_client, Client
from flask import current_app

class SupabaseClient:
    _instance: Client = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Retorna la instancia del cliente de Supabase.
        Implementa Singleton con Tipado Client.
        """
        if cls._instance is None:
            # Intentar obtener de app context (Flask)
            try:
                url = current_app.config.get('SUPABASE_URL')
                key = current_app.config.get('SUPABASE_KEY')
            except Exception:
                url = None
                key = None
            
            # Fallback a variables de entorno directas
            if not url or not key:
                url = os.environ.get("SUPABASE_URL")
                key = os.environ.get("SUPABASE_KEY")
                
            if url and key:
                try:
                    # Limpiar comillas si existen
                    url = url.replace('"', '').replace("'", "")
                    key = key.replace('"', '').replace("'", "")
                    
                    cls._instance = create_client(url, key)
                    print(f"[OK] Cliente Supabase inicializado: {url}")
                except Exception as e:
                    print(f"[ERROR] Fallo al inicializar cliente Supabase: {e}")
                    return None
            else:
                print("[WARN] No se detectaron SUPABASE_URL / SUPABASE_KEY para inicializar el cliente")
                return None
                
        return cls._instance

def get_db_connection_string():
    """
    Retorna el string de conexión para SQLAlchemy/Psycopg2.
    """
    try:
        uri = current_app.config.get('SUPABASE_DB_URI')
    except Exception:
        uri = None
        
    if not uri:
        uri = os.environ.get('SUPABASE_DB_URI')
        
    return uri.replace('"', '').replace("'", "") if uri else None


