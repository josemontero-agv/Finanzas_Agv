# -*- coding: utf-8 -*-
"""
Módulo Web (Frontend).

Mantiene rutas de compatibilidad que redirigen al frontend Next.js.
"""

from flask import Blueprint

# Definir el Blueprint web (sin prefix '/api/v1' porque sirve redirecciones)
web_bp = Blueprint('web', __name__, static_folder='../static')

# Importar rutas después de definir el blueprint
from app.web import routes

