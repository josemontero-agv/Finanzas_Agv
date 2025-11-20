# -*- coding: utf-8 -*-
"""
Módulo de Emails.

Maneja el envío de correos masivos y automatizados.

Features pendientes de implementación:
- Envío de letras por recuperar
- Envío de letras en banco
- Envío de constancias de detracción
- Templates de correos HTML
- Sistema de cola de correos
"""

from flask import Blueprint

# Definir el Blueprint de emails
emails_bp = Blueprint('emails', __name__, url_prefix='/api/v1/emails')

# Importar rutas después de definir el blueprint
from app.emails import routes

