# -*- coding: utf-8 -*-
"""
Rutas Web (Frontend).

Sirve las páginas HTML del sistema.
"""

from flask import render_template, request, redirect, url_for, session, flash
from app.web import web_bp


# =============================================================================
# AUTENTICACIÓN
# =============================================================================

@web_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Página de login.
    
    TODO: Conectar con API de autenticación
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # TODO: Llamar a /api/v1/auth/login
        # Por ahora, login dummy
        if username and password:
            session['username'] = username
            session['logged_in'] = True
            # Generar email basado en username (temporal hasta integración con Odoo)
            session['email'] = f"{username.lower().replace(' ', '.')}@agrovet.com.pe"
            flash('Login exitoso', 'success')
            return redirect(url_for('web.dashboard'))
        else:
            flash('Credenciales inválidas', 'danger')
    
    return render_template('login.html')


@web_bp.route('/logout')
def logout():
    """Cierra sesión del usuario."""
    session.clear()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('web.login'))


# =============================================================================
# DASHBOARD
# =============================================================================

@web_bp.route('/')
@web_bp.route('/dashboard')
def dashboard():
    """
    Dashboard principal con KPIs.
    
    TODO: Obtener datos de APIs para mostrar métricas
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('dashboard.html', username=session.get('username'))


# =============================================================================
# COBRANZAS
# =============================================================================

@web_bp.route('/collections/report-12')
def collections_report_12():
    """
    Reporte de Cuenta 12 - Cuentas por Cobrar.
    
    FUNCIONAL: Conectado con API
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('collections/report_account12.html')


@web_bp.route('/collections/report-national')
def collections_report_national():
    """
    Reporte Nacional de Cobranzas.
    
    TODO: Implementar vista
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('en_progreso.html')


@web_bp.route('/collections/report-international')
def collections_report_international():
    """
    Reporte Internacional de Cobranzas.
    
    TODO: Implementar vista
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('en_progreso.html')


@web_bp.route('/collections/dashboard')
def collections_dashboard():
    """
    Dashboard de Cobranzas con gráficos.
    
    TODO: Implementar dashboard interactivo
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('en_progreso.html')


# =============================================================================
# TESORERÍA
# =============================================================================

@web_bp.route('/treasury/report-42')
def treasury_report_42():
    """
    Reporte de Cuenta 42 - Cuentas por Pagar.
    
    FUNCIONAL: Conectado con API
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('treasury/report_account42.html')


@web_bp.route('/treasury/report-daily-payments')
def treasury_report_daily_payments():
    """
    Reporte de Pagos Diarios - Registros Abiertos.
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('treasury/report_daily_payments.html')


@web_bp.route('/treasury/report-supplier-banks')
def treasury_report_supplier_banks():
    """
    Reporte de Cuentas Bancarias de Proveedores.
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('treasury/report_supplier_banks.html')



@web_bp.route('/treasury/dashboard')
def treasury_dashboard():
    """
    Dashboard de Tesorería.
    
    TODO: Implementar dashboard interactivo
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('en_progreso.html')


# =============================================================================
# LETRAS
# =============================================================================

@web_bp.route('/letters/dashboard')
def letters_dashboard():
    """
    Dashboard de Letras.
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('letters/dashboard.html')


@web_bp.route('/letters/management')
def letters_management():
    """
    Gestión de Créditos - Envío de correos (Letras).
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('letters/manage.html')


@web_bp.route('/letters/to-recover')
def letters_to_recover():
    """
    Gestión de letras por recuperar (Redirect a Management).
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return redirect(url_for('web.letters_management'))


@web_bp.route('/letters/in-bank')
def letters_in_bank():
    """
    Gestión de letras en banco (Redirect a Management).
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return redirect(url_for('web.letters_management'))


# =============================================================================
# DETRACCIONES
# =============================================================================

@web_bp.route('/detractions/send-certificates')
def detractions_send():
    """
    Envío masivo de constancias de detracción.
    
    TODO: Implementar vista
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('en_progreso.html')


# =============================================================================
# DASHBOARD INTERDEPARTAMENTAL
# =============================================================================

@web_bp.route('/dashboard/interdepartmental')
def dashboard_interdepartmental():
    """
    Dashboard interdepartamental (Cobranzas + Tesorería).
    
    TODO: Implementar dashboard combinado
    """
    if not session.get('logged_in'):
        return redirect(url_for('web.login'))
    
    return render_template('en_progreso.html')

