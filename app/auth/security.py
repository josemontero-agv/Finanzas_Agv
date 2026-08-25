# -*- coding: utf-8 -*-
"""
Utilidades de seguridad para endpoints autenticados.
"""

from functools import wraps
from flask import jsonify, session
from flask_jwt_extended import (
    verify_jwt_in_request,
    get_jwt,
    get_jwt_identity,
    unset_jwt_cookies,
)


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
        if not (_has_valid_jwt() or session.get('logged_in')):
            return jsonify({
                'success': False,
                'message': 'Usuario no autenticado',
                'redirect': '/login'
            }), 401

        # Desactivar de verdad: si app_users.is_active=False, cortar sesión.
        # None = sin fila / Supabase caído → no bloquear (mismo criterio que OAuth).
        email = get_authenticated_user_email()
        if email:
            try:
                from app.apps.services import is_bootstrap_admin_email, is_user_active_in_db
                if (
                    not is_bootstrap_admin_email(email)
                    and is_user_active_in_db(email) is False
                ):
                    session.clear()
                    response = jsonify({
                        'success': False,
                        'message': 'Usuario desactivado',
                        'redirect': '/login',
                    })
                    unset_jwt_cookies(response)
                    return response, 401
            except Exception:
                pass

        return view_func(*args, **kwargs)
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
    Roles del usuario autenticado, en vivo desde ADMIN_EMAILS / app_users
    (mismo criterio que user-info y roles_claim_for_email). No depender solo
    del JWT stale: un cambio de rol en /apps aplica en el siguiente request.
    """
    email = get_authenticated_user_email()
    if email:
        try:
            from app.apps.services import roles_claim_for_email
            roles = roles_claim_for_email(email)
            if session.get('logged_in'):
                session['roles'] = roles
            return roles
        except Exception:
            pass

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

    Para rutas sensibles (observabilidad, centro de apps) usar require_admin /
    require_apps_operator, que SIEMPRE bloquean con 403 aunque RBAC_LOG_ONLY=True.
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


def _forbid_roles(required: list[str]):
    """403 inmediato (ignora RBAC_LOG_ONLY)."""
    import logging as _logging
    _rbac_logger = _logging.getLogger('finanzas_agv.rbac')
    user_roles = get_authenticated_user_roles() or []
    if required and not any(r in user_roles for r in required):
        _rbac_logger.warning(
            "RBAC hard-deny: usuario '%s' requiere %s (roles: %s)",
            session.get('username') or get_authenticated_user_email() or 'unknown',
            required,
            user_roles,
        )
        return jsonify({
            'success': False,
            'message': 'No tiene permisos para acceder a este recurso',
        }), 403
    return None


def require_admin(view_func):
    """
    Exige rol admin con bloqueo real (403), aunque RBAC_LOG_ONLY=True.
    Usar en Observabilidad / telemetría de personas.
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        denied = _forbid_roles(['admin'])
        if denied:
            return denied
        return view_func(*args, **kwargs)
    return wrapper


def require_apps_operator(view_func):
    """
    Exige admin o app_assistant con bloqueo real (403).
    Usar en Centro de aplicaciones (/api/v1/apps).
    """
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        denied = _forbid_roles(['admin', 'app_assistant'])
        if denied:
            return denied
        return view_func(*args, **kwargs)
    return wrapper
