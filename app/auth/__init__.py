# -*- coding: utf-8 -*-
"""
Módulo de Autenticación.

Maneja el login exclusivo con Google OAuth2 (restringido a dominio
corporativo + whitelist) y la sesión Flask del usuario autenticado.
"""

from flask import Blueprint

# Definir el Blueprint de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Importar rutas después de definir el blueprint para evitar imports circulares
from app.auth import routes
from app.auth import oauth
