# -*- coding: utf-8 -*-
"""
Módulo de Tesorería (Treasury).

Maneja reportes y operaciones de tesorería.
"""

from flask import Blueprint

# Definir el Blueprint de tesorería
treasury_bp = Blueprint('treasury', __name__, url_prefix='/api/v1/treasury')

# Importar rutas después de definir el blueprint para evitar imports circulares
from app.treasury import routes
