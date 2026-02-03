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
        - date_cutoff (str, optional): Fecha de corte para reporte histórico
        - supplier (str, optional): Nombre del proveedor a filtrar
        - account_codes (str, optional): Códigos de cuenta separados por coma
        - payment_state (str, optional): Estado de pago
        - only_vouchers (bool, optional): Solo mostrar comprobantes (excluir asientos manuales)
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
        date_cutoff = request.args.get('date_cutoff') # Nuevo
        supplier = request.args.get('supplier')
        account_codes = request.args.get('account_codes')
        payment_state = request.args.get('payment_state')
        doc_type_id = request.args.get('doc_type_id', type=int)
        reference = request.args.get('reference')
        has_retention = request.args.get('has_retention') == 'true' # Checkbox param
        has_origin = request.args.get('has_origin') == 'true' # Checkbox param
        only_vouchers = request.args.get('only_vouchers') == 'true' # Checkbox param: Solo Comprobantes
        include_reconciled = request.args.get('include_reconciled') == 'true' # Checkbox param
        if date_cutoff:
            # En corte histórico incluir conciliados para cuadrar con el mayor
            include_reconciled = True
        limit = request.args.get('limit', type=int, default=10000)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        # Obtener datos
        data = treasury_service.get_accounts_payable_report(
            start_date=date_from,
            end_date=date_to,
            cutoff_date=date_cutoff,
            supplier=supplier,
            limit=limit,
            account_codes=account_codes,
            payment_state=payment_state,
            doc_type_id=doc_type_id,
            reference=reference,
            has_retention=has_retention,
            has_origin=has_origin,
            only_vouchers=only_vouchers,
            include_reconciled=include_reconciled
        )
        
        def _summarize(rows):
            overall = {
                'debit': 0.0,
                'credit': 0.0,
                'pending_cutoff': 0.0,
                'paid_after_cutoff': 0.0,
                'saldo': 0.0,
                'count': 0
            }
            accounts = {}
            
            for row in rows:
                acc = row.get('account_code') or 'N/A'
                acc_name = row.get('account_name') or ''
                debit = float(row.get('debit', 0.0) or 0.0)
                credit = float(row.get('credit', 0.0) or 0.0)
                pending = float(row.get('amount_residual_historical', row.get('amount_residual', 0.0)) or 0.0)
                paid_after = float(row.get('paid_after_cutoff', 0.0) or 0.0)
                
                overall['debit'] += debit
                overall['credit'] += credit
                overall['pending_cutoff'] += pending
                overall['paid_after_cutoff'] += paid_after
                overall['count'] += 1
                
                if acc not in accounts:
                    accounts[acc] = {
                        'account_code': acc,
                        'account_name': acc_name,
                        'debit': 0.0,
                        'credit': 0.0,
                        'pending_cutoff': 0.0,
                        'paid_after_cutoff': 0.0,
                        'saldo': 0.0,
                        'count': 0
                    }
                accounts[acc]['debit'] += debit
                accounts[acc]['credit'] += credit
                accounts[acc]['pending_cutoff'] += pending
                accounts[acc]['paid_after_cutoff'] += paid_after
                accounts[acc]['count'] += 1
            
            # Calcular saldo (Debe - Haber) por cuenta y global
            # En Odoo el "Saldo" de análisis/mayor corresponde al balance = debit - credit.
            # Para cuentas de pasivo (42), normalmente será negativo (saldo acreedor).
            for acc_code, data_acc in accounts.items():
                data_acc['saldo'] = data_acc['debit'] - data_acc['credit']
            overall['saldo'] = overall['debit'] - overall['credit']

            by_account = list(accounts.values())
            by_account.sort(key=lambda x: x['account_code'])
            
            # Log para debug
            print(f"[DEBUG RESUMEN] Total registros: {overall['count']}")
            print(f"[DEBUG RESUMEN] Débito: {overall['debit']:.2f}")
            print(f"[DEBUG RESUMEN] Haber: {overall['credit']:.2f}")
            print(f"[DEBUG RESUMEN] Saldo: {overall['saldo']:.2f}")
            print(f"[DEBUG RESUMEN] Pendiente al corte: {overall['pending_cutoff']:.2f}")
            print(f"[DEBUG RESUMEN] Pagado después corte: {overall['paid_after_cutoff']:.2f}")
            print("[DEBUG RESUMEN] Cuentas encontradas: " + ', '.join([f"{a['account_code']} ({a['count']})" for a in by_account]))
            
            return {
                'overall': overall,
                'by_account': by_account
            }
        
        summary = _summarize(data)
        
        # Preparar filtros aplicados para la respuesta
        filters_applied = {
            'date_from': date_from,
            'date_to': date_to,
            'date_cutoff': date_cutoff,
            'supplier': supplier,
            'account_codes': account_codes,
            'payment_state': payment_state,
            'doc_type_id': doc_type_id,
            'reference': reference,
            'has_retention': has_retention,
            'has_origin': has_origin,
            'only_vouchers': only_vouchers,
            'include_reconciled': include_reconciled,
            'limit': limit
        }
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'summary': summary,
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


@treasury_bp.route('/report/account42-netted', methods=['GET'])
def report_account42_netted():
    """
    Endpoint para reporte de cuentas por pagar neteado (desde Supabase).
    
    Query Parameters:
        - supplier (str, optional): Nombre del proveedor a filtrar
    
    Response (JSON):
        {
            "success": true,
            "data": [...],
            "count": 123
        }
    """
    try:
        supplier = request.args.get('supplier')
        
        # Para este endpoint no necesitamos conectarnos a Odoo, solo a Supabase
        treasury_service = TreasuryService(None)
        data = treasury_service.get_netted_report_from_supabase(supplier=supplier)
        
        # Calcular resumen simple para compatibilidad con el frontend
        summary = {
            'overall': {
                'actual_balance': sum(float(row.get('actual_balance', 0)) for row in data),
                'original_amount': sum(float(row.get('original_amount', 0)) for row in data),
                'count': len(data)
            }
        }
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'summary': summary,
            'message': f'Reporte neteado generado con {len(data)} registros desde Supabase'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar reporte neteado: {str(e)}',
            'data': []
        }), 500


@treasury_bp.route('/report/supplier-banks', methods=['GET'])
def report_supplier_banks():
    """
    Endpoint para reporte de cuentas bancarias de proveedores.
    
    Query Parameters:
        - supplier (str, optional): Nombre del proveedor a filtrar
    
    Response (JSON):
        {
            "success": true,
            "data": [...]
        }
    """
    try:
        supplier = request.args.get('supplier')
        
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        data = treasury_service.get_supplier_bank_accounts(supplier_name=supplier)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'message': f'Se encontraron {len(data)} cuentas bancarias'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener cuentas bancarias: {str(e)}',
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


@treasury_bp.route('/filter-options', methods=['GET'])
def filter_options():
    """
    Endpoint para obtener las opciones de filtros (tipos de documento).
    """
    try:
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        filter_data = treasury_service.get_filter_options()
        
        return jsonify({
            'success': True,
            'data': filter_data,
            'message': 'Opciones de filtros obtenidas exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener opciones de filtros: {str(e)}',
            'data': {'document_types': []}
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
