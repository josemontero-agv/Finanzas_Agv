import os
from app import create_app

# Respeta el mismo entorno que run.py (APP_ENV/FLASK_ENV/ENV), en vez de forzar siempre
# 'development'. Así el worker/beat de Celery carga el .env correcto (desarrollo o
# producción) para el ETL y el resto de tareas.
_valid_environments = ('development', 'production', 'testing')
_environment = (os.getenv('APP_ENV') or os.getenv('FLASK_ENV') or os.getenv('ENV') or 'development').lower()
if _environment not in _valid_environments:
    _environment = 'development'

app = create_app(_environment)
celery = app.extensions["celery"]
