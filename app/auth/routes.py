# -*- coding: utf-8 -*-
"""
Rutas de Autenticacion.

Endpoints para login y autenticacion de usuarios.
"""

from flask import jsonify, session, current_app
from app.auth import auth_bp
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
    Endpoint para obtener informacion del usuario actual desde la sesion.

    Response (JSON):
        {
            "success": true,
            "username": "usuario",
            "email": "usuario@agrovet.com.pe"
        }
    """
    if session.get('logged_in'):
        return jsonify({
            'success': True,
            'username': session.get('username', ''),
            'email': session.get('email', '')
        }), 200
    return jsonify({
        'success': False,
        'message': 'Usuario no autenticado'
    }), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesion del usuario autenticado."""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Sesion cerrada'
    }), 200


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
        'endpoints': ['/google', '/google/callback', '/logout', '/status', '/user-info']
    }), 200
