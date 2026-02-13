# -*- coding: utf-8 -*-
"""
Rutas Web (Gateway hacia Frontend Next.js).

Mantiene compatibilidad con URLs historicas de Flask redirigiendo
al nuevo frontend en `frontend/`.
"""

from flask import request, redirect, session, jsonify
from app.web import web_bp
from app.core.supabase import SupabaseClient
from app.core.odoo import OdooRepository
from flask import current_app


# =============================================================================
# HEALTH CHECK (para Next.js)
# =============================================================================

@web_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint para verificar estado de los servicios.
    """
    try:
        # Verificar Odoo
        odoo_status = "disconnected"
        try:
            odoo_repo = OdooRepository(
                url=current_app.config.get('ODOO_URL'),
                db=current_app.config.get('ODOO_DB'),
                username=current_app.config.get('ODOO_USER'),
                password=current_app.config.get('ODOO_PASSWORD')
            )
            odoo_status = "connected" if odoo_repo.is_connected() else "disconnected"
        except:
            odoo_status = "error"
        
        # Verificar Supabase
        supabase_status = "connected" if SupabaseClient.get_client() else "disconnected"
        
        return jsonify({
            "status": "healthy",
            "version": "2.0.0",
            "services": {
                "odoo": odoo_status,
                "supabase": supabase_status
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

def _frontend_url(path='/'):
    """Construye URL absoluta al frontend Next.js."""
    base_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000').rstrip('/')
    safe_path = path if path.startswith('/') else f'/{path}'
    return f'{base_url}{safe_path}'


@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Redirige login legacy al frontend."""
    return redirect(_frontend_url('/login'))


@web_bp.route('/logout')
def logout():
    """Cierra sesion legacy y redirige al frontend."""
    session.clear()
    return redirect(_frontend_url('/login'))


# =============================================================================
# DASHBOARD
# =============================================================================

@web_bp.route('/')
@web_bp.route('/dashboard')
def dashboard():
    """Redirige dashboard legacy a Letras (modo restringido)."""
    return redirect(_frontend_url('/letters'))


# =============================================================================
# COBRANZAS
# =============================================================================

@web_bp.route('/collections/report-12')
def collections_report_12():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/collections/report-national')
def collections_report_national():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/collections/report-international')
def collections_report_international():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/collections/dashboard')
def collections_dashboard():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


# =============================================================================
# TESORERÍA
# =============================================================================

@web_bp.route('/treasury/report-42')
def treasury_report_42():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/treasury/report-daily-payments')
def treasury_report_daily_payments():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/treasury/report-supplier-banks')
def treasury_report_supplier_banks():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/treasury/dashboard')
def treasury_dashboard():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


# =============================================================================
# LETRAS
# =============================================================================

@web_bp.route('/letters/dashboard')
def letters_dashboard():
    """Redirige dashboard de letras legacy al frontend."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/letters/management')
def letters_management():
    """Redirige gestion de letras legacy al frontend."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/letters/to-recover')
def letters_to_recover():
    """Redirige ruta legacy de letras por recuperar al frontend."""
    return redirect(_frontend_url('/letters'))


@web_bp.route('/letters/in-bank')
def letters_in_bank():
    """Redirige ruta legacy de letras en banco al frontend."""
    return redirect(_frontend_url('/letters'))


# =============================================================================
# DETRACCIONES
# =============================================================================

@web_bp.route('/detractions/send-certificates')
def detractions_send():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))


# =============================================================================
# DASHBOARD INTERDEPARTAMENTAL
# =============================================================================

@web_bp.route('/dashboard/interdepartmental')
def dashboard_interdepartmental():
    """Redirige módulo no disponible hacia Letras."""
    return redirect(_frontend_url('/letters'))

