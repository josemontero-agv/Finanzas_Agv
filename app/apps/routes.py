# -*- coding: utf-8 -*-
"""
Rutas API del Centro de aplicaciones (/api/v1/apps).

Acceso: admin + app_assistant (bloqueo real, no solo RBAC_LOG_ONLY).
Reglas de usuarios:
  - app_assistant solo crea/edita role=user
  - no tocar emails en ADMIN_EMAILS
  - no asignar admin vía UI
"""

from typing import Optional

from flask import jsonify, request

from app.apps import apps_bp
from app.apps import services as apps_svc
from app.auth.security import (
    get_authenticated_user_email,
    get_authenticated_user_roles,
    require_apps_operator,
    require_login,
)
from app.core.telemetry import log_event


def _actor_roles() -> list:
    return get_authenticated_user_roles() or []


def _is_admin() -> bool:
    return 'admin' in _actor_roles()


def _is_assistant_only() -> bool:
    roles = _actor_roles()
    return 'app_assistant' in roles and 'admin' not in roles


def _forbid(message: str, status: int = 403):
    return jsonify({'success': False, 'message': message}), status


def _validate_user_mutation(
    target_email: str,
    desired_role: Optional[str],
    *,
    creating: bool,
):
    """Aplica reglas duras de rol sobre altas/ediciones."""
    target_email = apps_svc.normalize_email(target_email)

    if apps_svc.is_bootstrap_admin_email(target_email):
        return _forbid('No se puede modificar un email protegido de ADMIN_EMAILS')

    if desired_role == 'admin':
        return _forbid('No se puede asignar el rol admin vía UI')

    if _is_assistant_only():
        if desired_role and desired_role != 'user':
            return _forbid('El asistente solo puede gestionar usuarios con rol user')
        if not creating:
            existing = apps_svc.fetch_app_user(target_email)
            if existing and existing.get('role') != 'user':
                return _forbid('El asistente no puede editar usuarios que no sean role=user')
            if desired_role is None and existing and existing.get('role') != 'user':
                return _forbid('El asistente no puede editar usuarios que no sean role=user')

    return None


def _supabase_inventory_error_message(exc: Exception) -> str:
    err = str(exc)
    err_l = err.lower()
    if 'invalid api key' in err_l or "'code': 401" in err_l or '"code": 401' in err_l:
        return (
            'Supabase rechazó SUPABASE_KEY (Invalid API key). '
            'Verifique .env.produccion (no placeholder TODO_*) y reinicie Flask.'
        )
    if 'does not exist' in err_l or 'pgrst205' in err_l:
        return (
            'Faltan tablas de inventario. Aplique '
            'scripts/etl/supabase_schema_app_users.sql y '
            'scripts/etl/supabase_schema_app_platforms.sql.'
        )
    return f'No se pudo construir el dashboard de aplicaciones: {exc}'


def _actor_identity() -> tuple[str, Optional[str]]:
    email = get_authenticated_user_email() or 'unknown'
    username = email.split('@')[0] if email and email != 'unknown' else None
    return email, username


@apps_bp.route('/dashboard', methods=['GET'])
@require_login
@require_apps_operator
def get_dashboard():
    """KPIs + series de charts de inventario (sin telemetría de personas/horarios)."""
    try:
        data = apps_svc.build_dashboard()
        return jsonify({'success': True, 'data': data}), 200
    except Exception as exc:
        return jsonify({
            'success': False,
            'message': _supabase_inventory_error_message(exc),
        }), 500


@apps_bp.route('/platforms', methods=['GET'])
@require_login
@require_apps_operator
def get_platforms():
    try:
        platforms = apps_svc.enrich_platforms_with_health(apps_svc.list_platforms())
        return jsonify({'success': True, 'data': platforms}), 200
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@apps_bp.route('/platforms', methods=['POST'])
@require_login
@require_apps_operator
def post_platform():
    body = request.get_json(silent=True) or {}
    try:
        row = apps_svc.create_platform(body)
        return jsonify({'success': True, 'data': row}), 201
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@apps_bp.route('/platforms/<platform_id>', methods=['PATCH'])
@require_login
@require_apps_operator
def patch_platform(platform_id: str):
    body = request.get_json(silent=True) or {}
    try:
        row = apps_svc.update_platform(platform_id, body)
        return jsonify({'success': True, 'data': row}), 200
    except LookupError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 404
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@apps_bp.route('/users', methods=['GET'])
@require_login
@require_apps_operator
def get_users():
    try:
        users = apps_svc.list_users()
        return jsonify({'success': True, 'data': users}), 200
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500


@apps_bp.route('/users', methods=['POST'])
@require_login
@require_apps_operator
def post_user():
    body = request.get_json(silent=True) or {}
    email = apps_svc.normalize_email(body.get('email'))
    role = (body.get('role') or 'user').strip().lower()

    if _is_assistant_only():
        role = 'user'

    err = _validate_user_mutation(email, role, creating=True)
    if err:
        return err

    if role == 'app_assistant' and not _is_admin():
        return _forbid('Solo un admin puede asignar app_assistant')

    try:
        row = apps_svc.create_user(
            email=email,
            display_name=body.get('display_name'),
            role=role,
            is_active=bool(body.get('is_active', True)),
            created_by=get_authenticated_user_email() or 'unknown',
        )
        actor_email, actor_username = _actor_identity()
        log_event(
            email=actor_email,
            category='users',
            name='user_created',
            payload={
                'target_email': row.get('email'),
                'role': row.get('role'),
                'is_active': row.get('is_active'),
            },
            path='/api/v1/apps/users',
            user_agent=request.headers.get('User-Agent'),
            username=actor_username,
        )
        return jsonify({'success': True, 'data': row}), 201
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except apps_svc.DuplicateUserError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 409
    except Exception as exc:
        msg = str(exc)
        status = 409 if 'duplicate' in msg.lower() or 'unique' in msg.lower() else 500
        if status == 409:
            msg = f'Ya existe un usuario con el email {email}'
        return jsonify({'success': False, 'message': msg}), status


@apps_bp.route('/users/<path:email>', methods=['PATCH'])
@require_login
@require_apps_operator
def patch_user(email: str):
    body = request.get_json(silent=True) or {}
    target = apps_svc.normalize_email(email)
    desired_role = body.get('role')
    if desired_role is not None:
        desired_role = str(desired_role).strip().lower()

    err = _validate_user_mutation(target, desired_role, creating=False)
    if err:
        return err

    if desired_role == 'app_assistant' and not _is_admin():
        return _forbid('Solo un admin puede asignar app_assistant')

    # Asistente: forzar que no cambie el rol a nada distinto de user
    if _is_assistant_only() and desired_role is not None:
        body = {**body, 'role': 'user'}

    tracked_keys = [
        k for k in ('display_name', 'role', 'is_active')
        if k in body and body[k] is not None
    ]
    previous = apps_svc.fetch_app_user(target)

    try:
        row = apps_svc.update_user(target, body)
        actor_email, actor_username = _actor_identity()
        is_toggle_only = tracked_keys == ['is_active']
        if is_toggle_only:
            log_event(
                email=actor_email,
                category='users',
                name='user_toggled',
                payload={
                    'target_email': target,
                    'is_active': row.get('is_active'),
                },
                path=f'/api/v1/apps/users/{target}',
                user_agent=request.headers.get('User-Agent'),
                username=actor_username,
            )
        elif tracked_keys:
            log_event(
                email=actor_email,
                category='users',
                name='user_updated',
                payload={
                    'target_email': target,
                    'fields': tracked_keys,
                    'old': {k: (previous or {}).get(k) for k in tracked_keys},
                    'new': {k: row.get(k) for k in tracked_keys},
                },
                path=f'/api/v1/apps/users/{target}',
                user_agent=request.headers.get('User-Agent'),
                username=actor_username,
            )
        return jsonify({'success': True, 'data': row}), 200
    except LookupError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 404
    except ValueError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 400
    except apps_svc.PersistenceError as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500
    except Exception as exc:
        return jsonify({'success': False, 'message': str(exc)}), 500
