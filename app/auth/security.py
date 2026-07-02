# -*- coding: utf-8 -*-
"""
Utilidades de seguridad para endpoints autenticados.
"""

from functools import wraps
from flask import jsonify, session


def require_login(view_func):
    """
    Decorador para exigir sesión autenticada en endpoints API.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'message': 'Usuario no autenticado',
                'redirect': '/login'  # Enviamos una pista al frontend
            }), 401
        return view_func(*args, **kwargs)
    return wrapper


def get_authenticated_user_email():
    """
    Retorna el email del usuario autenticado en sesión.
    """
    return (session.get('email') or '').strip().lower()


def require_role(*roles):
    """
    Decorador RBAC que verifica roles en sesion.
    
    NOTA: En este ciclo el decorador solo verifica, no bloquea.
    Cuando RBAC este completamente configurado con grupos de Odoo,
    cambiar `log_only=True` a `log_only=False` en la configuracion.
    Esto permite desplegar la infraestructura sin riesgo de bloquear usuarios.
    """
    import logging as _logging
    _rbac_logger = _logging.getLogger('finanzas_agv.rbac')

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            from flask import current_app
            log_only = current_app.config.get('RBAC_LOG_ONLY', True)
            user_roles = session.get('roles', [])
            required = list(roles)

            if required and not any(r in user_roles for r in required):
                _rbac_logger.warning(
                    "RBAC: usuario '%s' accedio a recurso que requiere roles %s (roles actuales: %s)",
                    session.get('username', 'unknown'),
                    required,
                    user_roles
                )
                if not log_only:
                    return jsonify({
                        'success': False,
                        'message': 'No tiene permisos para acceder a este recurso'
                    }), 403
            return view_func(*args, **kwargs)
        return wrapper
    return decorator

