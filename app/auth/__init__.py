# -*- coding: utf-8 -*-
"""
Módulo de Autenticación.

Maneja la autenticación de usuarios contra Odoo.
"""

from flask import Blueprint

# Definir el Blueprint de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Importar rutas después de definir el blueprint para evitar imports circulares
from app.auth import routes
