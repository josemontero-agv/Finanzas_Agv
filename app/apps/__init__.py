# -*- coding: utf-8 -*-
"""
Centro de aplicaciones: inventario de plataformas + gestión de usuarios RBAC.

Visible a admin y app_assistant. Observabilidad/telemetría de personas queda
fuera de este módulo (solo admin en /api/v1/analytics).
"""

from flask import Blueprint

apps_bp = Blueprint('apps', __name__, url_prefix='/api/v1/apps')

from app.apps import routes  # noqa: E402, F401
