# -*- coding: utf-8 -*-
"""
Módulo de Letras de Cambio (Bills of Exchange).

Maneja la generación de planillas y gestión de letras.

Features pendientes de implementación:
- Generación de planillas de letras para banco
- Consulta de letras por vencer
- Consulta de letras en banco
- Exportación a formato bancario
- Seguimiento de estado de letras
"""

from flask import Blueprint

# Definir el Blueprint de letras
letters_bp = Blueprint('letters', __name__, url_prefix='/api/v1/letters')

# Importar rutas después de definir el blueprint
from app.letters import routes

