# -*- coding: utf-8 -*-
"""
Rutas de Autenticacion.

Endpoints para login y autenticacion de usuarios.
"""

from flask import jsonify, request, session, current_app
from flask_jwt_extended import (
    jwt_required,
    create_access_token,
    set_access_cookies,
    unset_jwt_cookies,
)
from app.auth import auth_bp
from app.auth.security import get_authenticated_user_email, get_authenticated_user_roles
from app.core.telemetry import log_event
from app import limiter


def _normalize_user_email(username, provided_email=None):
    """
    Normaliza email corporativo del usuario autenticado.
    Si el username ya es email, lo usa; de lo contrario agrega el dominio corporativo.
    """
    domain = current_app.config.get('USER_EMAIL_DOMAIN', 'agrovetmarket.com').strip().lower()
    candidate = (provided_email or username or '').strip().lower()

    if '@' in candidate:
        return candidate
    if candidate:
        return f'{candidate}@{domain}'
    return ''


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute;50 per hour")
def login():
    """
    Endpoint de login legado (usuario/contraseña contra Odoo). Deshabilitado.

    El único método de autenticación soportado es Google OAuth2, vía
    GET /api/v1/auth/google. Se conserva esta ruta (en vez de eliminarla)
    para no romper integraciones externas que aún la invoquen.

    Response (JSON):
        {
            "success": false,
            "message": "Este método de login ya no está disponible. Use /api/v1/auth/google"
        }
    """
    return jsonify({
        'success': False,
        'message': 'Este método de login ya no está disponible. Use /api/v1/auth/google'
    }), 410


@auth_bp.route('/user-info', methods=['GET'])
def user_info():
    """
    Endpoint para obtener informacion del usuario actual desde la sesion o el JWT.

    Los roles se resuelven en vivo (ADMIN_EMAILS / app_users) para que el sidebar
    refleje admin/app_assistant sin depender solo de claims JWT antiguos.
    """
    from app.apps import services as apps_svc

    def _live_roles(email: str, fallback=None):
        email = (email or '').strip().lower()
        if email:
            roles = apps_svc.roles_claim_for_email(email)
            # Mantener sesión alineada con el rol efectivo.
            if session.get('logged_in'):
                session['roles'] = roles
            return roles
        return fallback or get_authenticated_user_roles() or []

    if session.get('logged_in'):
        email = session.get('email', '')
        return jsonify({
            'success': True,
            'username': session.get('username', ''),
            'email': email,
            'roles': _live_roles(email, session.get('roles')),
        }), 200

    email = get_authenticated_user_email()
    if email:
        return jsonify({
            'success': True,
            'username': email.split('@')[0],
            'email': email,
            'roles': _live_roles(email),
        }), 200

    return jsonify({
        'success': False,
        'message': 'Usuario no autenticado'
    }), 401


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Reemite un access token JWT nuevo a partir de un refresh token válido (cookie HttpOnly).

    El frontend puede invocar este endpoint cuando reciba un 401 en llamadas API para
    renovar la sesión sin forzar un nuevo login con Google.
    """
    from flask_jwt_extended import get_jwt_identity, get_jwt

    identity = get_jwt_identity()
    claims = get_jwt()
    additional_claims = {
        'email': claims.get('email', ''),
        'roles': claims.get('roles', []),
    }
    response = jsonify({'success': True, 'message': 'Token renovado'})
    new_access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    set_access_cookies(response, new_access_token)
    return response, 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesion del usuario autenticado e invalida las cookies JWT (access + refresh)."""
    # Telemetría ANTES de session.clear() para conservar identidad.
    email = get_authenticated_user_email() or (session.get('email') or '').strip().lower()
    username = session.get('username') or (email.split('@')[0] if email else None)
    if email:
        log_event(
            email=email,
            category='auth',
            name='user_logout',
            payload={},
            path='/api/v1/auth/logout',
            user_agent=request.headers.get('User-Agent'),
            username=username,
        )

    session.clear()
    response = jsonify({
        'success': True,
        'message': 'Sesion cerrada'
    })
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route('/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado del modulo de autenticacion.

    Response (JSON):
        {
            "module": "auth",
            "status": "active",
            "endpoints": ["/google", "/google/callback", "/logout", "/status", "/user-info"]
        }
    """
    return jsonify({
        'module': 'auth',
        'status': 'active',
        'endpoints': ['/google', '/google/callback', '/logout', '/status', '/user-info', '/refresh']
    }), 200
