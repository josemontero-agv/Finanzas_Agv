# -*- coding: utf-8 -*-
"""
Servicios del Centro de aplicaciones: app_users + app_platforms + health.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Optional

from flask import current_app

from app.core.supabase import SupabaseClient

logger = logging.getLogger('finanzas_agv.apps')

VALID_ROLES = frozenset({'admin', 'app_assistant', 'user'})
VALID_PLATFORM_KINDS = frozenset({'finanzas_agv', 'odoo', 'other'})
APPS_OPERATOR_ROLES = frozenset({'admin', 'app_assistant'})


class DuplicateUserError(Exception):
    """El email ya existe en app_users (respuesta 409)."""


class PersistenceError(RuntimeError):
    """El UPDATE no se reflejó en la fila leída (no devolver 200 con datos viejos)."""


def _client():
    return SupabaseClient.get_client()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_email(email: Optional[str]) -> str:
    return (email or '').strip().lower()


def get_admin_emails() -> list[str]:
    return [
        normalize_email(e)
        for e in (current_app.config.get('ADMIN_EMAILS') or [])
        if normalize_email(e)
    ]


def is_bootstrap_admin_email(email: str) -> bool:
    return normalize_email(email) in get_admin_emails()


def corporate_email_domain() -> str:
    try:
        return (current_app.config.get('USER_EMAIL_DOMAIN') or 'agrovetmarket.com').strip().lower()
    except RuntimeError:
        return 'agrovetmarket.com'


def assert_corporate_email(email: str) -> None:
    """Exige dominio corporativo (mismo criterio que el gate OAuth)."""
    domain = corporate_email_domain()
    email = normalize_email(email)
    if not email or '@' not in email or not email.endswith(f'@{domain}'):
        raise ValueError(
            f'El email debe pertenecer al dominio corporativo @{domain}'
        )


def fetch_app_user(email: str) -> Optional[dict]:
    """Devuelve la fila de app_users o None si no existe / Supabase caído."""
    email = normalize_email(email)
    if not email:
        return None
    client = _client()
    if not client:
        return None
    try:
        res = (
            client.table('app_users')
            .select('email,display_name,role,is_active,created_by,created_at,updated_at')
            .eq('email', email)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        return rows[0] if rows else None
    except Exception as exc:
        logger.warning('No se pudo leer app_users para %s: %s', email, exc)
        return None


def is_user_active_in_db(email: str) -> Optional[bool]:
    """
    Estado de acceso en app_users:
      True  → fila activa
      False → fila existe e is_active=False (denegar, no fallback)
      None  → sin fila, sin cliente o error (usar fallback ALLOWED_USERS)
    """
    email = normalize_email(email)
    if not email:
        return None
    client = _client()
    if not client:
        return None
    try:
        res = (
            client.table('app_users')
            .select('email,is_active')
            .eq('email', email)
            .limit(1)
            .execute()
        )
        rows = res.data or []
        if not rows:
            return None
        return bool(rows[0].get('is_active'))
    except Exception as exc:
        logger.warning('is_user_active_in_db falló para %s: %s', email, exc)
        return None


def resolve_primary_role(email: str) -> str:
    """
    Rol único efectivo: ADMIN_EMAILS → siempre admin.
    Si no, role de app_users (default user).
    """
    email = normalize_email(email)
    if is_bootstrap_admin_email(email):
        return 'admin'

    row = fetch_app_user(email)
    if row and row.get('role') in VALID_ROLES:
        return row['role']
    return 'user'


def roles_claim_for_email(email: str) -> list[str]:
    """JWT/session: un solo rol primario (no mezclar admin+user)."""
    return [resolve_primary_role(email)]


def serialize_user(row: dict) -> dict:
    """Marca filas no editables (ADMIN_EMAILS o role admin)."""
    out = dict(row)
    email = normalize_email(out.get('email'))
    out['is_protected'] = is_bootstrap_admin_email(email) or (out.get('role') == 'admin')
    return out


def list_users() -> list[dict]:
    client = _client()
    if not client:
        return []
    try:
        res = (
            client.table('app_users')
            .select('email,display_name,role,is_active,created_by,created_at,updated_at')
            .order('email')
            .execute()
        )
        return [serialize_user(r) for r in (res.data or [])]
    except Exception as exc:
        logger.exception('list_users falló: %s', exc)
        raise


def create_user(
    *,
    email: str,
    display_name: Optional[str],
    role: str,
    is_active: bool,
    created_by: str,
) -> dict:
    email = normalize_email(email)
    role = (role or 'user').strip().lower()
    if role not in VALID_ROLES:
        raise ValueError(f'Rol inválido: {role}')
    if not email or '@' not in email:
        raise ValueError('Email inválido')
    assert_corporate_email(email)

    client = _client()
    if not client:
        raise RuntimeError('Supabase no disponible')

    if fetch_app_user(email):
        raise DuplicateUserError(f'Ya existe un usuario con el email {email}')

    payload = {
        'email': email,
        'display_name': (display_name or email.split('@')[0]).strip(),
        'role': role,
        'is_active': bool(is_active),
        'created_by': normalize_email(created_by) or 'system',
        'updated_at': _now_iso(),
    }
    try:
        res = client.table('app_users').insert(payload).execute()
    except Exception as exc:
        msg = str(exc).lower()
        if 'duplicate' in msg or 'unique' in msg or '23505' in msg:
            raise DuplicateUserError(f'Ya existe un usuario con el email {email}') from exc
        raise
    rows = res.data or []
    if not rows:
        raise RuntimeError('No se pudo crear el usuario')
    return serialize_user(rows[0])


def update_user(email: str, patch: dict) -> dict:
    email = normalize_email(email)
    client = _client()
    if not client:
        raise RuntimeError('Supabase no disponible')

    allowed: dict[str, Any] = {}
    if 'display_name' in patch and patch['display_name'] is not None:
        allowed['display_name'] = str(patch['display_name']).strip()
    if 'role' in patch and patch['role'] is not None:
        role = str(patch['role']).strip().lower()
        if role not in VALID_ROLES:
            raise ValueError(f'Rol inválido: {role}')
        allowed['role'] = role
    if 'is_active' in patch and patch['is_active'] is not None:
        allowed['is_active'] = bool(patch['is_active'])

    if not allowed:
        raise ValueError('Sin campos para actualizar')

    expected = dict(allowed)
    allowed['updated_at'] = _now_iso()
    res = (
        client.table('app_users')
        .update(allowed)
        .eq('email', email)
        .execute()
    )
    rows = res.data or []
    if rows:
        updated = serialize_user(rows[0])
        _assert_patch_persisted(updated, expected)
        return updated

    # Algunos clientes/RLS no devuelven filas en UPDATE aunque sí aplique:
    # re-leer y comparar contra el patch para no devolver 200 con datos viejos.
    existing = fetch_app_user(email)
    if existing:
        updated = serialize_user(existing)
        _assert_patch_persisted(updated, expected)
        return updated
    raise LookupError('Usuario no encontrado')


def _assert_patch_persisted(row: dict, expected: dict) -> None:
    """Falla si is_active/role/display_name del re-fetch no coinciden con el patch."""
    mismatches: list[str] = []
    for key, want in expected.items():
        if key == 'updated_at':
            continue
        got = row.get(key)
        if key == 'is_active':
            if bool(got) != bool(want):
                mismatches.append(key)
        elif key == 'display_name':
            if str(got or '').strip() != str(want or '').strip():
                mismatches.append(key)
        elif got != want:
            mismatches.append(key)
    if mismatches:
        raise PersistenceError(
            'La actualización no se persistió en Supabase '
            f'(campos sin cambio: {", ".join(mismatches)}). '
            'Verifique RLS y que SUPABASE_KEY sea la service role.'
        )


def list_platforms() -> list[dict]:
    client = _client()
    if not client:
        return []
    try:
        res = (
            client.table('app_platforms')
            .select('id,name,slug,base_url,kind,is_active,sort_order,notes,created_at,updated_at')
            .order('sort_order')
            .order('name')
            .execute()
        )
        return list(res.data or [])
    except Exception as exc:
        logger.exception('list_platforms falló: %s', exc)
        raise


def create_platform(data: dict) -> dict:
    client = _client()
    if not client:
        raise RuntimeError('Supabase no disponible')

    name = (data.get('name') or '').strip()
    slug = (data.get('slug') or '').strip().lower().replace(' ', '-')
    kind = (data.get('kind') or 'other').strip().lower()
    if not name or not slug:
        raise ValueError('name y slug son obligatorios')
    if kind not in VALID_PLATFORM_KINDS:
        raise ValueError(f'kind inválido: {kind}')

    payload = {
        'name': name,
        'slug': slug,
        'base_url': (data.get('base_url') or None),
        'kind': kind,
        'is_active': bool(data.get('is_active', True)),
        'sort_order': int(data.get('sort_order') or 100),
        'notes': data.get('notes'),
        'updated_at': _now_iso(),
    }
    res = client.table('app_platforms').insert(payload).execute()
    rows = res.data or []
    if not rows:
        raise RuntimeError('No se pudo crear la plataforma')
    return rows[0]


def update_platform(platform_id: str, patch: dict) -> dict:
    client = _client()
    if not client:
        raise RuntimeError('Supabase no disponible')

    allowed: dict[str, Any] = {}
    for key in ('name', 'base_url', 'notes'):
        if key in patch and patch[key] is not None:
            allowed[key] = patch[key] if key != 'name' else str(patch[key]).strip()
    if 'slug' in patch and patch['slug'] is not None:
        allowed['slug'] = str(patch['slug']).strip().lower().replace(' ', '-')
    if 'kind' in patch and patch['kind'] is not None:
        kind = str(patch['kind']).strip().lower()
        if kind not in VALID_PLATFORM_KINDS:
            raise ValueError(f'kind inválido: {kind}')
        allowed['kind'] = kind
    if 'is_active' in patch and patch['is_active'] is not None:
        allowed['is_active'] = bool(patch['is_active'])
    if 'sort_order' in patch and patch['sort_order'] is not None:
        allowed['sort_order'] = int(patch['sort_order'])

    if not allowed:
        raise ValueError('Sin campos para actualizar')

    allowed['updated_at'] = _now_iso()
    res = (
        client.table('app_platforms')
        .update(allowed)
        .eq('id', platform_id)
        .execute()
    )
    rows = res.data or []
    if not rows:
        raise LookupError('Plataforma no encontrada')
    return rows[0]


def probe_live_health() -> dict[str, str]:
    """
    Reutiliza la lógica de /api/health: odoo + supabase (Finanzas AGV).
    Valores: ok | down | unknown
    """
    result = {'finanzas_agv': 'unknown', 'odoo': 'unknown'}

    try:
        from app.core.odoo import OdooRepository

        odoo_repo = OdooRepository(
            url=current_app.config.get('ODOO_URL'),
            db=current_app.config.get('ODOO_DB'),
            username=current_app.config.get('ODOO_USER'),
            password=current_app.config.get('ODOO_PASSWORD'),
        )
        result['odoo'] = 'ok' if odoo_repo.is_connected() else 'down'
    except Exception:
        result['odoo'] = 'down'

    try:
        result['finanzas_agv'] = 'ok' if SupabaseClient.ping() else 'down'
    except Exception:
        result['finanzas_agv'] = 'down'

    return result


def enrich_platforms_with_health(platforms: list[dict]) -> list[dict]:
    live = probe_live_health()
    checked_at = _now_iso()
    enriched = []
    for p in platforms:
        kind = p.get('kind') or 'other'
        row = dict(p)
        if kind in ('finanzas_agv', 'odoo'):
            status = live.get(kind, 'unknown')
        else:
            # Sin health endpoint: unknown si activa, down si inactiva
            status = 'unknown' if p.get('is_active', True) else 'down'
        row['health_status'] = status
        row['health_checked_at'] = checked_at
        enriched.append(row)
    return enriched


def build_dashboard() -> dict:
    users = list_users()
    platforms = enrich_platforms_with_health(list_platforms())

    role_counts = Counter((u.get('role') or 'user') for u in users)
    active = sum(1 for u in users if u.get('is_active'))
    inactive = len(users) - active

    health_counts = Counter((p.get('health_status') or 'unknown') for p in platforms)
    active_platforms = sum(1 for p in platforms if p.get('is_active'))

    # Altas por día (últimos 30 días) desde created_at — inventario, no telemetría de navegación
    by_day: dict[str, int] = defaultdict(int)
    for u in users:
        created = u.get('created_at') or ''
        day = str(created)[:10]
        if len(day) == 10:
            by_day[day] += 1
    users_created_by_day = [
        {'date': d, 'count': by_day[d]} for d in sorted(by_day.keys())[-30:]
    ]

    return {
        'kpis': {
            'users_total': len(users),
            'users_active': active,
            'users_inactive': inactive,
            'users_by_role': {
                'admin': role_counts.get('admin', 0),
                'app_assistant': role_counts.get('app_assistant', 0),
                'user': role_counts.get('user', 0),
            },
            'platforms_total': len(platforms),
            'platforms_active': active_platforms,
            'platforms_ok': health_counts.get('ok', 0),
            'platforms_degraded': health_counts.get('degraded', 0),
            'platforms_down': health_counts.get('down', 0),
            'platforms_unknown': health_counts.get('unknown', 0),
        },
        'charts': {
            'roles_distribution': [
                {'role': 'admin', 'count': role_counts.get('admin', 0)},
                {'role': 'app_assistant', 'count': role_counts.get('app_assistant', 0)},
                {'role': 'user', 'count': role_counts.get('user', 0)},
            ],
            'users_active_inactive': [
                {'status': 'activos', 'count': active},
                {'status': 'inactivos', 'count': inactive},
            ],
            'platforms_health': [
                {
                    'name': p.get('name') or p.get('slug'),
                    'status': p.get('health_status') or 'unknown',
                    'value': 1 if p.get('health_status') == 'ok' else (
                        0 if p.get('health_status') == 'down' else 0.5
                    ),
                }
                for p in platforms
            ],
            'users_created_by_day': users_created_by_day,
        },
        'platforms': platforms,
        'users': users,
    }
