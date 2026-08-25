# -*- coding: utf-8 -*-
"""
Rutas de autenticación con Google OAuth2.

Flujo completo (redirect a Google, callback, validación e inicio de sesión)
manejado por el backend Flask. Al finalizar, redirige al navegador hacia el
frontend Next.js (FRONTEND_URL) con la cookie de sesión Flask ya establecida.
"""

from flask import current_app, redirect, request, session, url_for
from flask_jwt_extended import create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies
from app import oauth
from app.auth import auth_bp
from app.auth.routes import _normalize_user_email
from app.core.telemetry import log_event


def _is_email_allowed(email):
    """
    Valida dominio corporativo + autorización de acceso.

    Preferencia: fila activa en app_users (Supabase).
    Fallback temporal: ALLOWED_USERS (env) si Supabase no está disponible
    o la tabla aún no está sembrada para ese email pero sí está en env.
    """
    from app.apps import services as apps_svc

    domain = current_app.config.get('USER_EMAIL_DOMAIN', 'agrovetmarket.com').strip().lower()
    email = (email or '').strip().lower()

    if not email or not email.endswith(f'@{domain}'):
        return False

    # Override bootstrap: ADMIN_EMAILS siempre permitido (aunque falte fila).
    if apps_svc.is_bootstrap_admin_email(email):
        return True

    active = apps_svc.is_user_active_in_db(email)
    if active is True:
        return True
    if active is False:
        # Fila existe pero inactiva → denegar (no caer a ALLOWED_USERS).
        return False

    # Supabase no disponible / error de lectura → fallback ALLOWED_USERS.
    allowed_users = current_app.config.get('ALLOWED_USERS', [])
    return email in allowed_users


def _roles_for_email(email):
    """
    Rol único primario: ['admin'] | ['app_assistant'] | ['user'].

    - Si email ∈ ADMIN_EMAILS → siempre admin (no se mezcla con user).
    - Si no, role de app_users (default user).
    """
    from app.apps import services as apps_svc
    return apps_svc.roles_claim_for_email(email)


@auth_bp.route('/google')
def google_login():
    """Inicia el flujo de login con Google redirigiendo al consentimiento."""
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/google/callback')
def google_callback():
    """
    Recibe el code de Google, valida la identidad y establece la sesión Flask.

    Si el email es válido (dominio + app_users activo / fallback ALLOWED_USERS),
    fija la sesión y redirige al frontend ya autenticado. Caso contrario,
    redirige al login del frontend con el error correspondiente en la query string.
    """
    frontend_url = (current_app.config.get('FRONTEND_URL') or 'http://localhost:3000').rstrip('/')
    user_agent = request.headers.get('User-Agent')

    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo') or {}
    except Exception:
        log_event(
            email='unknown',
            category='auth',
            name='user_login_failure',
            payload={'error_code': 'google_auth_failed'},
            path='/api/v1/auth/google/callback',
            user_agent=user_agent,
        )
        return redirect(f'{frontend_url}/login?error=google_auth_failed')

    email = (user_info.get('email') or '').strip().lower()

    if not user_info.get('email_verified', True) or not _is_email_allowed(email):
        log_event(
            email=email or 'unknown',
            category='auth',
            name='user_login_failure',
            payload={'error_code': 'not_allowed'},
            path='/api/v1/auth/google/callback',
            user_agent=user_agent,
            username=(user_info.get('name') or (email.split('@')[0] if email else None)),
        )
        session.clear()
        return redirect(f'{frontend_url}/login?error=not_allowed')

    username = (user_info.get('name') or email.split('@')[0])
    user_email = _normalize_user_email(username, email)
    roles = _roles_for_email(user_email)

    session['logged_in'] = True
    session['username'] = username
    session['email'] = user_email
    session['roles'] = roles
    session.permanent = True

    log_event(
        email=user_email,
        category='auth',
        name='user_login_success',
        payload={'username': username},
        path='/api/v1/auth/google/callback',
        user_agent=user_agent,
        username=username,
    )

    response = redirect(f'{frontend_url}/collections')

    # JWT real como cookies HttpOnly (access de corta duración + refresh de larga duración).
    # Complementa la sesión Flask para que llamadas cross-site entre dominios distintos
    # (backend y frontend en Render) no dependan solo de la cookie de sesión.
    additional_claims = {
        'email': user_email,
        'roles': roles,
    }
    access_token = create_access_token(identity=username, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=username, additional_claims=additional_claims)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)

    return response
