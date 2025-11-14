# -*- coding: utf-8 -*-
"""
Módulo de Cobranzas (Collections).

Maneja reportes y operaciones de cuentas por cobrar.
"""

from flask import Blueprint

# Definir el Blueprint de cobranzas
collections_bp = Blueprint('collections', __name__, url_prefix='/api/v1/collections')

# Importar rutas después de definir el blueprint para evitar imports circulares
from app.collections import routes
