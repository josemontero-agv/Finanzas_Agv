"""
Módulo de conexión con Supabase.
Provee la instancia del cliente y utilidades de base de datos.
"""
import os
from supabase import create_client, Client
from flask import current_app


def _is_placeholder_key(key: str | None) -> bool:
    """Detecta placeholders típicos en overlays .env.supabase.* (TODO_*, etc.)."""
    if not key:
        return True
    upper = key.strip().upper()
    return (
        upper.startswith('TODO')
        or 'TODO_' in upper
        or upper in {'CHANGE_ME', 'CHANGEME', 'XXX', 'YOUR_SERVICE_ROLE_KEY'}
        or 'PEGAR' in upper
    )


class SupabaseClient:
    _instance: Client = None

    @classmethod
    def reset_client(cls) -> None:
        """Invalida el singleton (p. ej. tras corregir SUPABASE_KEY y reiniciar flujos)."""
        cls._instance = None

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

                    if _is_placeholder_key(key):
                        print(
                            "[ERROR] SUPABASE_KEY es un placeholder (TODO_*). "
                            "Usa la secret key real en .env.produccion y reinicia Flask."
                        )
                        return None

                    cls._instance = create_client(url, key)
                    print(f"[OK] Cliente Supabase inicializado: {url}")
                except Exception as e:
                    print(f"[ERROR] Fallo al inicializar cliente Supabase: {e}")
                    return None
            else:
                print("[WARN] No se detectaron SUPABASE_URL / SUPABASE_KEY para inicializar el cliente")
                return None

        return cls._instance

    @classmethod
    def ping(cls) -> bool:
        """Comprueba que el cliente pueda consultar PostgREST (no solo existir)."""
        client = cls.get_client()
        if not client:
            return False
        try:
            client.table('app_users').select('email').limit(1).execute()
            return True
        except Exception:
            return False

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


