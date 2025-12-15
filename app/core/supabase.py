# -*- coding: utf-8 -*-
"""
Módulo de conexión con Supabase.
Provee la instancia del cliente y utilidades de base de datos.
"""
import os
from supabase import create_client, Client
from flask import current_app

class SupabaseClient:
    _instance = None
    
    @classmethod
    def get_client(cls) -> Client:
        """
        Retorna la instancia del cliente de Supabase.
        Implementa Singleton.
        """
        if cls._instance is None:
            url = current_app.config.get('SUPABASE_URL')
            key = current_app.config.get('SUPABASE_KEY')
            
            if not url or not key:
                # Fallback a variables de entorno directas si estamos fuera de app context
                url = os.getenv('SUPABASE_URL')
                key = os.getenv('SUPABASE_KEY')
                
            if url and key:
                try:
                    cls._instance = create_client(url, key)
                    print("[OK] Cliente Supabase inicializado")
                except Exception as e:
                    print(f"[ERROR] Fallo al conectar con Supabase: {e}")
                    return None
            else:
                print("[WARN] No se encontraron credenciales SUPABASE_URL / SUPABASE_KEY")
                return None
                
        return cls._instance

def get_db_connection_string():
    """
    Retorna el string de conexión para SQLAlchemy/Psycopg2.
    """
    return current_app.config.get('SUPABASE_DB_URI') or os.getenv('SUPABASE_DB_URI')

