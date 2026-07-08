# -*- coding: utf-8 -*-
"""
Utilidades de seguridad para endpoints autenticados.
"""

from functools import wraps
from flask import jsonify, session
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity


def _has_valid_jwt():
    """
    Intenta validar un JWT presente en las cookies del request (access token).

    Devuelve True si hay un JWT válido y no expirado. No lanza excepción si no
    hay JWT o si es inválido/expiró: en ese caso se debe caer a la sesión Flask.
    """
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return False
    return get_jwt_identity() is not None


def require_login(view_func):
    """
    Decorador para exigir sesión autenticada en endpoints API.

    Acepta CUALQUIERA de los dos mecanismos de autenticación:
    - Sesión Flask válida (session['logged_in'], cookie de sesión clásica).
    - JWT válido (cookie HttpOnly emitida por app/auth/oauth.py con Flask-JWT-Extended).

    Esto permite que llamadas cross-site entre dominios distintos (backend y frontend
    desplegados por separado en Render) no dependan únicamente de la cookie de sesión
    con SameSite=None, que algunos navegadores/entornos bloquean con más frecuencia.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if _has_valid_jwt() or session.get('logged_in'):
            return view_func(*args, **kwargs)
        return jsonify({
            'success': False,
            'message': 'Usuario no autenticado',
            'redirect': '/login'  # Enviamos una pista al frontend
        }), 401
    return wrapper


def get_authenticated_user_email():
    """
    Retorna el email del usuario autenticado, ya sea desde la sesión Flask o desde
    los claims del JWT (según cuál de los dos mecanismos haya autenticado el request).
    """
    session_email = (session.get('email') or '').strip().lower()
    if session_email:
        return session_email

    try:
        claims = get_jwt()
        return (claims.get('email') or '').strip().lower()
    except Exception:
        return ''


def get_authenticated_user_roles():
    """
    Retorna la lista de roles del usuario autenticado, desde el claim "roles" del JWT
    o desde la sesión Flask (session['roles']) si no hay JWT.

    Base para activar RBAC (ver require_role más abajo): hoy los roles solo se loguean.
    """
    try:
        claims = get_jwt()
        jwt_roles = claims.get('roles')
        if jwt_roles:
            return jwt_roles
    except Exception:
        pass
    return session.get('roles', [])


def require_role(*roles):
    """
    Decorador RBAC que verifica roles (JWT claim "roles" o session['roles']).

    NOTA: En este ciclo el decorador solo verifica, no bloquea (RBAC_LOG_ONLY=True).
    Cuando RBAC este completamente configurado con grupos de Odoo / listas de administradores
    verificadas, cambiar RBAC_LOG_ONLY a False en config.py (o vía variable de entorno) para que
    el bloqueo 403 se aplique de verdad. Esto permite desplegar la infraestructura de roles sin
    riesgo de bloquear usuarios mientras se termina de definir la matriz de permisos.
    """
    import logging as _logging
    _rbac_logger = _logging.getLogger('finanzas_agv.rbac')

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            from flask import current_app
            log_only = current_app.config.get('RBAC_LOG_ONLY', True)
            user_roles = get_authenticated_user_roles()
            required = list(roles)

            if required and not any(r in user_roles for r in required):
                _rbac_logger.warning(
                    "RBAC: usuario '%s' accedio a recurso que requiere roles %s (roles actuales: %s)",
                    session.get('username') or get_authenticated_user_email() or 'unknown',
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
