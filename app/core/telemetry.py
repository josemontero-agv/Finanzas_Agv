# -*- coding: utf-8 -*-
"""
Telemetría de uso de la aplicación (product analytics).

Persiste eventos en Supabase (`user_activity_logs`) vía service role.
Los fallos se registran en el logger y NUNCA deben romper flujos críticos
(login, logout, navegación).
"""

import logging
from typing import Any, Optional

from app.core.supabase import SupabaseClient

logger = logging.getLogger('finanzas_agv.telemetry')


def log_event(
    email: str,
    category: str,
    name: str,
    payload: Optional[dict] = None,
    path: Optional[str] = None,
    user_agent: Optional[str] = None,
    username: Optional[str] = None,
) -> bool:
    """
    Inserta un evento de actividad en Supabase.

    Returns:
        True si el insert fue exitoso; False si falló (solo se loguea).
    """
    try:
        client = SupabaseClient.get_client()
        if not client:
            logger.warning(
                "Telemetría omitida (sin cliente Supabase): %s/%s",
                category,
                name,
            )
            return False

        row: dict[str, Any] = {
            'user_email': (email or 'unknown').strip().lower() or 'unknown',
            'username': username,
            'event_category': category,
            'event_name': name,
            'payload': payload or {},
            'path': path,
            'user_agent': user_agent,
        }
        client.table('user_activity_logs').insert(row).execute()
        return True
    except Exception as exc:
        logger.warning(
            "Fallo al registrar evento %s/%s: %s",
            category,
            name,
            exc,
            exc_info=False,
        )
        return False
