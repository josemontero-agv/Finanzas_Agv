# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

# Path absoluto
env_path = r"C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\Finanzas_Agv\.env.produccion"

print(f"--- Diagnóstico ---")
print(f"Archivo existe: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print(f"Tamaño: {os.path.getsize(env_path)} bytes")
    # Intentar cargar
    load_dotenv(env_path, override=True)
    
    print(f"Llaves en os.environ:")
    keys = ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_DB_URI", "ODOO_URL"]
    for k in keys:
        val = os.getenv(k)
        found = "SÍ" if val else "NO"
        # Mostrar solo los primeros 4 caracteres para verificar carga sin exponer secretos
        prefix = val[:4] + "..." if val else ""
        print(f"  {k}: {found} {prefix}")
else:
    print(f"Directorio actual: {os.getcwd()}")
    print(f"Contenido de la raíz (si existe):")
    root = r"C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\Finanzas_Agv"
    if os.path.exists(root):
        print(os.listdir(root))

