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
                'message': 'Usuario no autenticado'
            }), 401
        return view_func(*args, **kwargs)
    return wrapper


def get_authenticated_user_email():
    """
    Retorna el email del usuario autenticado en sesión.
    """
    return (session.get('email') or '').strip().lower()

