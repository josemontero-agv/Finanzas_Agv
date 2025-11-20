# -*- coding: utf-8 -*-
"""
Módulo Web (Frontend).

Sirve las vistas HTML con Bootstrap para la interfaz de usuario.
"""

from flask import Blueprint

# Definir el Blueprint web (sin prefix '/api/v1' porque sirve HTML)
web_bp = Blueprint('web', __name__, template_folder='../templates', static_folder='../static')

# Importar rutas después de definir el blueprint
from app.web import routes

