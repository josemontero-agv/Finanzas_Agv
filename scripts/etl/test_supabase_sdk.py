# -*- coding: utf-8 -*-
"""
Script de prueba de conexión a Supabase vía SDK.
Verifica que SUPABASE_URL y SUPABASE_KEY sean correctos.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

# Cargar variables de entorno
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

url = os.getenv('SUPABASE_URL', '').replace('"', '').replace("'", "")
key = os.getenv('SUPABASE_KEY', '').replace('"', '').replace("'", "")

if not url or not key:
    print("[ERROR] SUPABASE_URL o SUPABASE_KEY no están definidos en .env.produccion")
    exit(1)

print(f"[INFO] Intentando conectar a: {url}")

try:
    # Opciones para el cliente
    options = {
        "auto_refresh_token": False,
        "persist_session": False,
        "headers": {}
    }
    
    # Inicializar el cliente con opciones y verify=False solo si es necesario (debugging)
    # Nota: supabase-py v2 usa httpx o requests por debajo.
    # Intentamos pasar opciones de transporte si es posible, pero create_client es simple.
    
    # Intento 1: Cliente estándar
    # supabase = create_client(url, key)
    
    # Intento 2: Cliente con httpx context (si hay problemas de SSL por VPN corporativa)
    import httpx
    transport = httpx.HTTPTransport(verify=False)
    # supabase = create_client(url, key, options=ClientOptions(transport=transport)) # Hypothetical
    
    # Como create_client no expone transport facilmente en v2, usamos la variable de entorno
    # para deshabilitar verificación SSL TEMPORALMENTE solo para este test
    import ssl
    ssl._create_default_https_context = ssl._create_unverified_context
    
    supabase = create_client(url, key)
    
    # Intentar una operación simple
    response = supabase.table('dim_partners').select("*", count='exact').limit(1).execute()
    
    print("\n" + "="*40)
    print("CONEXION EXITOSA")
    print(f"Registros encontrados en dim_partners: {response.count}")
    print("="*40)
    
except Exception as e:
    print("\n" + "="*40)
    print("ERROR DE CONEXION")
    print(f"Detalle: {str(e)}")
    print("="*40)
    print("\nSugerencias:")
    print("1. Revisa que SUPABASE_KEY sea la 'service_role' key (debe empezar con eyJ...).")
    print("2. Tu clave actual parece ser una Management Key (sb_secret...), esa no sirve aqui.")
    print("3. Copia la clave desde Settings -> API -> service_role.")

