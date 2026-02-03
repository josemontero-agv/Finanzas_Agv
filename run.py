# -*- coding: utf-8 -*-
"""
Punto de entrada de la aplicación Finanzas AGV.

Uso:
    # Modo desarrollo (por defecto)
    python run.py
    
    # Modo producción
    python run.py production
    
    # Modo testing
    python run.py testing
"""

import sys
import os
from app import create_app

# Determinar el entorno desde argumentos o variable de entorno
env_from_args = sys.argv[1] if len(sys.argv) > 1 else None
env_from_vars = (
    os.getenv('APP_ENV') or
    os.getenv('FLASK_ENV') or
    os.getenv('ENV')
)

environment = (env_from_args or env_from_vars or 'development').lower()

# Validar entorno
valid_environments = ['development', 'production', 'testing']
if environment not in valid_environments:
    print(f"[ERROR] Entorno inválido: {environment}")
    print(f"[INFO] Entornos válidos: {', '.join(valid_environments)}")
    sys.exit(1)

# Crear aplicación
app = create_app(environment)

if __name__ == '__main__':
    # Configuración del servidor de desarrollo
    if environment == 'development':
        print("\n" + "="*60)
        print("  FINANZAS AGV - API REST")
        print("  Entorno: DESARROLLO")
        print("="*60 + "\n")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    elif environment == 'production':
        print("\n" + "="*60)
        print("  FINANZAS AGV - API REST")
        print("  Entorno: PRODUCCIÓN")
        print("  ADVERTENCIA: Usa gunicorn o uWSGI en producción real")
        print("  Ejemplo (Gunicorn): gunicorn --bind 0.0.0.0:5000 run:app")
        print("  Ejemplo (uWSGI):    uwsgi --http :5000 --module run:app")
        print("="*60 + "\n")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True
        )
    else:
        # Testing mode
        print("\n" + "="*60)
        print("  FINANZAS AGV - API REST")
        print("  Entorno: TESTING")
        print("="*60 + "\n")
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True
        )

