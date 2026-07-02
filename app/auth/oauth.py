# -*- coding: utf-8 -*-
"""
Rutas de autenticación con Google OAuth2.

Flujo completo (redirect a Google, callback, validación e inicio de sesión)
manejado por el backend Flask. Al finalizar, redirige al navegador hacia el
frontend Next.js (FRONTEND_URL) con la cookie de sesión Flask ya establecida.
"""

from flask import current_app, redirect, session, url_for
from flask_jwt_extended import create_access_token
from app import oauth
from app.auth import auth_bp
from app.auth.routes import _normalize_user_email


def _is_email_allowed(email):
    """Valida que el email pertenezca al dominio corporativo Y esté en la whitelist."""
    domain = current_app.config.get('USER_EMAIL_DOMAIN', 'agrovetmarket.com').strip().lower()
    allowed_users = current_app.config.get('ALLOWED_USERS', [])

    if not email or not email.endswith(f'@{domain}'):
        return False
    return email in allowed_users


@auth_bp.route('/google')
def google_login():
    """Inicia el flujo de login con Google redirigiendo al consentimiento."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """
    Recibe el code de Google, valida la identidad y establece la sesión Flask.

    Si el email es válido (dominio corporativo + whitelist ALLOWED_USERS),
    fija la sesión y redirige al frontend ya autenticado. Caso contrario,
    redirige al login del frontend con el error correspondiente en la query string.
    """
    frontend_url = (current_app.config.get('FRONTEND_URL') or 'http://localhost:3000').rstrip('/')

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo') or {}
    except Exception:
        return redirect(f'{frontend_url}/login?error=google_auth_failed')

    email = (user_info.get('email') or '').strip().lower()

    if not user_info.get('email_verified', True) or not _is_email_allowed(email):
        session.clear()
        return redirect(f'{frontend_url}/login?error=not_allowed')

    username = (user_info.get('name') or email.split('@')[0])
    user_email = _normalize_user_email(username, email)

    session['logged_in'] = True
    session['username'] = username
    session['email'] = user_email
    session.permanent = True

    # JWT real (se mantiene por compatibilidad; el frontend no lo usa, depende de la cookie de sesión)
    create_access_token(
        identity=username,
        additional_claims={
            'email': user_email,
            'type': 'access',
        }
    )

    return redirect(f'{frontend_url}/collections')
