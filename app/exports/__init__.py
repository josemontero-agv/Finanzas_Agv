# -*- coding: utf-8 -*-
"""
Módulo de Exportación.

Maneja la exportación de datos a diferentes formatos (Excel, PDF, CSV).
"""

from flask import Blueprint

# Definir el Blueprint de exportación
exports_bp = Blueprint('exports', __name__, url_prefix='/api/v1/exports')

# Importar rutas después de definir el blueprint
from app.exports import routes

