# -*- coding: utf-8 -*-
"""
Rutas de Tesorería (Treasury).

Endpoints para reportes de cuentas por pagar (CxP).
"""

from flask import request, jsonify, current_app
from app.treasury import treasury_bp
from app.treasury.services import TreasuryService
from app.core.odoo import OdooRepository


def _get_odoo_repository():
    """Helper para crear instancia de OdooRepository desde la configuración."""
    try:
        return OdooRepository(
            url=current_app.config['ODOO_URL'],
            db=current_app.config['ODOO_DB'],
            username=current_app.config['ODOO_USER'],
            password=current_app.config['ODOO_PASSWORD']
        )
    except ValueError as e:
        raise ValueError(f"Error de configuración de Odoo: {str(e)}")


@treasury_bp.route('/report/account42', methods=['GET'])
def report_account42():
    """
    Endpoint para reporte de cuentas por pagar (Cuenta 42 y 43).
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial (formato: YYYY-MM-DD)
        - date_to (str, optional): Fecha final (formato: YYYY-MM-DD)
        - supplier (str, optional): Nombre del proveedor a filtrar
        - account_codes (str, optional): Códigos de cuenta separados por coma
        - payment_state (str, optional): Estado de pago
        - limit (int, optional): Límite de registros (default: 10000)
    
    Response (JSON):
        {
            "success": true,
            "data": [...],
            "count": 123,
            "filters": {...}
        }
    """
    try:
        # Obtener parámetros de query
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        supplier = request.args.get('supplier')
        account_codes = request.args.get('account_codes')
        payment_state = request.args.get('payment_state')
        limit = request.args.get('limit', type=int, default=10000)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        # Obtener datos
        data = treasury_service.get_accounts_payable_report(
            start_date=date_from,
            end_date=date_to,
            supplier=supplier,
            limit=limit,
            account_codes=account_codes,
            payment_state=payment_state
        )
        
        # Preparar filtros aplicados para la respuesta
        filters_applied = {
            'date_from': date_from,
            'date_to': date_to,
            'supplier': supplier,
            'account_codes': account_codes,
            'payment_state': payment_state,
            'limit': limit
        }
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'filters': filters_applied,
            'message': f'Reporte de CxP generado exitosamente con {len(data)} registros'
        }), 200
        
    except ValueError as ve:
        return jsonify({
            'success': False,
            'message': str(ve),
            'data': []
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar reporte de CxP: {str(e)}',
            'data': []
        }), 500


@treasury_bp.route('/summary/by-supplier', methods=['GET'])
def summary_by_supplier():
    """
    Endpoint para resumen de CxP agrupado por proveedor.
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial
        - date_to (str, optional): Fecha final
    
    Response (JSON):
        {
            "success": true,
            "data": [{
                "supplier_name": "...",
                "total_debt": 123.45,
                "total_overdue": 45.67,
                "count_invoices": 5,
                "oldest_invoice_days": 45
            }, ...],
            "count": 10
        }
    """
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        data = treasury_service.get_summary_by_supplier(date_from, date_to)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'message': f'Resumen por proveedor generado con {len(data)} proveedores'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar resumen por proveedor: {str(e)}',
            'data': []
        }), 500


@treasury_bp.route('/summary/by-aging', methods=['GET'])
def summary_by_aging():
    """
    Endpoint para resumen de CxP agrupado por antigüedad.
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial
        - date_to (str, optional): Fecha final
    
    Response (JSON):
        {
            "success": true,
            "data": {
                "Vigente": {"count": 10, "amount": 1234.56},
                "Atraso Corto (1-30)": {...},
                ...
            }
        }
    """
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        data = treasury_service.get_summary_by_aging(date_from, date_to)
        
        return jsonify({
            'success': True,
            'data': data,
            'message': 'Resumen por antigüedad generado exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar resumen por antigüedad: {str(e)}',
            'data': {}
        }), 500


@treasury_bp.route('/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado del módulo de tesorería.
    
    Response (JSON):
        {
            "module": "treasury",
            "status": "active",
            "endpoints": [...]
        }
    """
    return jsonify({
        'module': 'treasury',
        'status': 'active',
        'implementation_status': 'complete',
        'endpoints': [
            '/report/account42',
            '/summary/by-supplier',
            '/summary/by-aging',
            '/status'
        ],
        'note': 'Módulo de tesorería implementado - Cuentas 42 y 43'
    }), 200
