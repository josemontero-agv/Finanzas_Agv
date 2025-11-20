# -*- coding: utf-8 -*-
"""
Módulo de Detracciones.

Maneja constancias de detracción y envío masivo.

Features pendientes de implementación:
- Obtener constancias de detracción desde Odoo
- Generación de PDFs de constancias
- Envío masivo de constancias por correo
- Seguimiento de envíos
- Reportes de detracciones
"""

from flask import Blueprint

# Definir el Blueprint de detracciones
detractions_bp = Blueprint('detractions', __name__, url_prefix='/api/v1/detractions')

# Importar rutas después de definir el blueprint
from app.detractions import routes

