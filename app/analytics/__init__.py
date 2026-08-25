# -*- coding: utf-8 -*-
"""
Módulo de Analytics / Observabilidad de uso.

Endpoints para registrar eventos de telemetría y consultar agregados (admin).
"""

from flask import Blueprint

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')

from app.analytics import routes  # noqa: E402, F401
