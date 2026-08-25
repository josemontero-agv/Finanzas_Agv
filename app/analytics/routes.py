# -*- coding: utf-8 -*-
"""
Rutas de Analytics (product analytics v1).

POST /events  — cualquier usuario autenticado (identidad desde sesión/JWT).
GET  /summary — solo administradores (bloqueo explícito aunque RBAC_LOG_ONLY=True).
"""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import jsonify, request, session
from flask_jwt_extended import get_jwt_identity

from app.analytics import analytics_bp
from app.auth.security import (
    get_authenticated_user_email,
    require_admin,
    require_login,
)
from app.core.supabase import SupabaseClient
from app.core.telemetry import log_event

KNOWN_MODULES = (
    'collections',
    'letters',
    'treasury',
    'dashboard',
    'diagnostics',
    'observability',
    'apps',
)

USER_ADMIN_EVENTS = frozenset({'user_created', 'user_updated', 'user_toggled'})
RECENT_EVENTS_LIMIT = 50
USER_ADMIN_ACTIONS_LIMIT = 50


def _lima_tz():
    try:
        return ZoneInfo('America/Lima')
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=-5))


LIMA_TZ = _lima_tz()


def _module_from_path(path: Optional[str]) -> str:
    if not path:
        return 'other'
    segment = path.strip('/').split('/', 1)[0].lower()
    return segment if segment in KNOWN_MODULES else 'other'


def _authenticated_username(email: str) -> str:
    username = (session.get('username') or '').strip()
    if username:
        return username
    try:
        identity = get_jwt_identity()
        if identity:
            return str(identity)
    except Exception:
        pass
    return email.split('@')[0] if email else 'unknown'


def _parse_date_bound(value: Optional[str], end_of_day: bool = False) -> Optional[datetime]:
    """Interpreta YYYY-MM-DD como día calendario en America/Lima."""
    if not value:
        return None
    try:
        day = datetime.strptime(value[:10], '%Y-%m-%d').date()
    except ValueError:
        return None
    if end_of_day:
        return datetime(day.year, day.month, day.day, 23, 59, 59, 999999, tzinfo=LIMA_TZ)
    return datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=LIMA_TZ)


def _as_lima(created_at: str) -> Optional[datetime]:
    if not created_at:
        return None
    try:
        ts = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(LIMA_TZ)
    except Exception:
        return None


def _serialize_event(row: dict) -> dict:
    payload = row.get('payload') or {}
    if not isinstance(payload, dict):
        payload = {}
    return {
        'created_at': row.get('created_at'),
        'user_email': row.get('user_email'),
        'username': row.get('username'),
        'event_category': row.get('event_category'),
        'event_name': row.get('event_name'),
        'payload': payload,
        'path': row.get('path'),
    }


@analytics_bp.route('/events', methods=['POST'])
@require_login
def create_event():
    """
    Registra un evento de uso. La identidad la fija el servidor (nunca el body).

    Body JSON:
        {
            "event_category": "nav",
            "event_name": "page_view",
            "payload": { "path": "/collections", "module": "collections" },
            "path": "/collections"
        }
    """
    data = request.get_json(silent=True) or {}
    category = (data.get('event_category') or '').strip()
    name = (data.get('event_name') or '').strip()

    if not category or not name:
        return jsonify({
            'success': False,
            'message': 'event_category y event_name son obligatorios',
        }), 400

    email = get_authenticated_user_email()
    if not email:
        return jsonify({
            'success': False,
            'message': 'Usuario no autenticado',
            'redirect': '/login',
        }), 401

    payload = data.get('payload') if isinstance(data.get('payload'), dict) else {}
    path = data.get('path') or payload.get('path')
    username = _authenticated_username(email)
    user_agent = request.headers.get('User-Agent')

    ok = log_event(
        email=email,
        category=category,
        name=name,
        payload=payload,
        path=path,
        user_agent=user_agent,
        username=username,
    )
    return jsonify({'success': True, 'recorded': ok}), 200


@analytics_bp.route('/summary', methods=['GET'])
@require_login
@require_admin
def get_summary():
    """
    Agregados de uso para el tablero /observability (solo admin).

    Query: from=YYYY-MM-DD&to=YYYY-MM-DD (default: últimos 30 días).
    Bloqueo real vía require_admin (ignora RBAC_LOG_ONLY).
    """
    now = datetime.now(LIMA_TZ)
    date_to = _parse_date_bound(request.args.get('to'), end_of_day=True) or now
    date_from = _parse_date_bound(request.args.get('from'))
    if date_from is None:
        start = date_to.astimezone(LIMA_TZ) - timedelta(days=30)
        date_from = start.replace(hour=0, minute=0, second=0, microsecond=0)

    if date_from > date_to:
        return jsonify({
            'success': False,
            'message': 'El parámetro from no puede ser posterior a to',
        }), 400

    client = SupabaseClient.get_client()
    if not client:
        return jsonify({
            'success': False,
            'message': 'Cliente Supabase no disponible',
        }), 503

    try:
        # PostgREST limita por defecto; paginamos para rangos amplios.
        rows: list[dict] = []
        page_size = 1000
        offset = 0
        from_iso = date_from.isoformat()
        to_iso = date_to.isoformat()

        while True:
            resp = (
                client.table('user_activity_logs')
                .select('user_email,username,event_category,event_name,payload,path,created_at')
                .gte('created_at', from_iso)
                .lte('created_at', to_iso)
                .order('created_at', desc=False)
                .range(offset, offset + page_size - 1)
                .execute()
            )
            batch = resp.data or []
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
            if offset > 100_000:
                break
    except Exception as exc:
        err = str(exc)
        err_l = err.lower()
        if 'invalid api key' in err_l or "'code': 401" in err_l or '"code": 401' in err_l:
            message = (
                'Supabase rechazó SUPABASE_KEY (Invalid API key). '
                'Verifique que .env.produccion tenga la secret key real (no TODO_* del overlay) '
                'y reinicie Flask.'
            )
        elif 'does not exist' in err_l or 'pgrst205' in err_l or 'user_activity_logs' in err_l:
            message = (
                'No se pudo consultar user_activity_logs. '
                'Aplique scripts/etl/supabase_schema_user_activity.sql en Supabase.'
            )
        else:
            message = f'Error al consultar actividad: {exc}'
        return jsonify({
            'success': False,
            'message': message,
        }), 500

    unique_users: set[str] = set()
    total_logins = 0
    total_failed_logins = 0
    total_logouts = 0
    total_page_views = 0
    active_days: set[str] = set()
    logins_by_hour = Counter()
    logins_by_day = Counter()
    user_login_counts: Counter = Counter()
    user_last_seen: dict[str, str] = {}
    module_views: Counter = Counter()
    user_admin_actions: list[dict] = []

    for row in rows:
        email = (row.get('user_email') or '').strip().lower()
        event_name = row.get('event_name') or ''
        created_at = row.get('created_at') or ''
        lima_ts = _as_lima(created_at)
        day_key = lima_ts.date().isoformat() if lima_ts else (created_at[:10] if created_at else '')

        if email and email != 'unknown':
            unique_users.add(email)
        if day_key:
            active_days.add(day_key)

        if email and created_at:
            prev = user_last_seen.get(email)
            if not prev or created_at > prev:
                user_last_seen[email] = created_at

        if event_name == 'user_login_success':
            total_logins += 1
            if email:
                user_login_counts[email] += 1
            if lima_ts:
                logins_by_hour[lima_ts.hour] += 1
            if day_key:
                logins_by_day[day_key] += 1

        elif event_name == 'user_login_failure':
            total_failed_logins += 1

        elif event_name == 'user_logout':
            total_logouts += 1

        elif event_name == 'page_view':
            total_page_views += 1
            payload = row.get('payload') or {}
            module = None
            if isinstance(payload, dict):
                module = payload.get('module')
            if not module:
                module = _module_from_path(row.get('path') or (payload.get('path') if isinstance(payload, dict) else None))
            module_views[module] += 1

        if event_name in USER_ADMIN_EVENTS:
            payload = row.get('payload') or {}
            if not isinstance(payload, dict):
                payload = {}
            user_admin_actions.append({
                'created_at': created_at,
                'actor_email': email,
                'event_name': event_name,
                'target_email': payload.get('target_email'),
                'payload': payload,
            })

    hours = [{'hour': h, 'count': int(logins_by_hour.get(h, 0))} for h in range(24)]

    # Serie diaria continua en el rango (días calendario Lima)
    days_series = []
    cursor = date_from.astimezone(LIMA_TZ).date()
    end_day = date_to.astimezone(LIMA_TZ).date()
    while cursor <= end_day:
        key = cursor.isoformat()
        days_series.append({'date': key, 'count': int(logins_by_day.get(key, 0))})
        cursor += timedelta(days=1)

    top_users = [
        {
            'email': email,
            'login_count': count,
            'last_seen': user_last_seen.get(email),
        }
        for email, count in user_login_counts.most_common(20)
    ]

    top_modules = [
        {'module': module, 'views': views}
        for module, views in module_views.most_common(20)
    ]

    recent_events = [
        _serialize_event(r) for r in reversed(rows[-RECENT_EVENTS_LIMIT:])
    ]
    user_admin_actions.reverse()
    user_admin_actions = user_admin_actions[:USER_ADMIN_ACTIONS_LIMIT]

    return jsonify({
        'success': True,
        'data': {
            'kpis': {
                'unique_users': len(unique_users),
                'total_logins': total_logins,
                'failed_logins': total_failed_logins,
                'logouts': total_logouts,
                'total_page_views': total_page_views,
                'active_days': len(active_days),
            },
            'logins_by_hour': hours,
            'logins_by_day': days_series,
            'top_users': top_users,
            'top_modules': top_modules,
            'recent_events': recent_events,
            'user_admin_actions': user_admin_actions,
            'range': {
                'from': date_from.astimezone(LIMA_TZ).date().isoformat(),
                'to': date_to.astimezone(LIMA_TZ).date().isoformat(),
                'timezone': 'America/Lima',
            },
        },
    }), 200
