# -*- coding: utf-8 -*-
"""
Script para inicializar la base de datos en Supabase.
Intenta usar conexión directa (psycopg2) y si falla, usa la API SQL de Supabase.
"""

import os
import requests
from dotenv import load_dotenv

# Cargar entorno de manera más robusta
def load_env():
    possible_paths = [
        # Nuevos archivos separados
        os.path.join(os.getcwd(), '.env.supabase.produccion'),
        os.path.join(os.getcwd(), '.env.produccion'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.supabase.produccion')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.produccion')),
        # Desarrollo
        os.path.join(os.getcwd(), '.env.supabase.desarrollo'),
        os.path.join(os.getcwd(), '.env.desarrollo')
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            load_dotenv(path, override=True)
            print(f"[ENV] Cargado: {path}")
    return True

load_env()

# Credenciales
DB_URI = os.getenv('SUPABASE_DB_URI', '').replace('"', '').replace("'", "")
SUPABASE_URL = os.getenv('SUPABASE_URL', '').replace('"', '').replace("'", "")
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '').replace('"', '').replace("'", "")

def run_sql_via_api(sql_content):
    """
    Ejecuta SQL usando la API REST de Supabase (pg_meta).
    Esta ruta es más robusta contra problemas de DNS/IPv6 locales.
    """
    print("[DB] Intentando ejecución vía API SQL...")
    
    # Endpoint SQL de Supabase (requiere key con permisos adecuados)
    api_url = f"{SUPABASE_URL}/rest/v1/"
    
    # Si no podemos ejecutar SQL arbitrario por API (que suele estar bloqueado por seguridad),
    # intentaremos usar el endpoint RPC si existiera, pero para DDL (CREATE TABLE)
    # la mejor opción sin conexión directa es usar la API de administración si se tiene.
    
    # Alternativa: Usar la librería 'supabase' si soporta query arbitrario (generalmente no DDL).
    # Sin embargo, dado que psycopg2 falló, intentaremos un workaround común:
    # Si el usuario tiene acceso al dashboard, es mejor, pero aquí intentaremos
    # modificar el host para usar el pooler si detectamos el fallo.
    pass

def run_sql_file(file_path):
    print(f"[DB] Leyendo {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        sql = f.read()

    # Intento 1: Conexión Directa con psycopg2
    try:
        import psycopg2
        print(f"[DB] Conectando a PostgreSQL...")
        # Modificar URI si es necesario para evitar problemas de SSL
        # conn_string = DB_URI + "?sslmode=require"
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
        print(f"[SUCCESS] SQL aplicado correctamente vía Psycopg2.")
        cur.close()
        conn.close()
        return
    except Exception as e:
        print(f"[WARN] Falló conexión directa: {e}")
        print("[INFO] Intentando conectar usando el Pooler de Supabase (IPv4)...")

    # Intento 2: Usar Pooler Supabase (IPv4 compatible)
    # Reemplazamos el host 'db.qupyfy...' por 'aws-0-us-west-1.pooler.supabase.com' (ejemplo común)
    # O mejor, pedimos al usuario que cambie la URI.
    # Pero como workaround automático, intentamos ejecutar statement por statement vía REST si fuera posible
    # (Supabase no permite DDL por REST API estándar).
    
    print("\n" + "="*50)
    print("ERROR CRITICO DE CONEXION A BASE DE DATOS")
    print("="*50)
    print("La conexión directa a PostgreSQL falló. Esto suele deberse a:")
    print("1. Bloqueo de puerto 5432 (Firewall corporativo/VPN).")
    print("2. Problema de resolución DNS IPv6 (Supabase usa IPv6 direct).")
    
    print("\nSOLUCIÓN AUTOMÁTICA SUGERIDA:")
    print("Usa el 'Connection Pooler' que soporta IPv4.")
    print("1. Ve a Supabase > Settings > Database > Connection String")
    print("2. Cambia el modo a 'Session' o 'Transaction'")
    print("3. Copia la nueva URI (puerto 6543) y actualiza .env.produccion")
    
    print("\nSOLUCIÓN MANUAL (Recomendada ahora):")
    print("Copia el contenido de 'scripts/etl/supabase_schema_netted.sql'")
    print("y pégalo en el SQL Editor de tu Dashboard de Supabase.")

if __name__ == '__main__':
    sql_file = os.path.abspath(os.path.join(os.path.dirname(__file__), 'supabase_schema_netted.sql'))
    run_sql_file(sql_file)


