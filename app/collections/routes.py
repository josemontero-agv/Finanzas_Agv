# -*- coding: utf-8 -*-
"""
Rutas de Cobranzas (Collections).

Endpoints para reportes de cuentas por cobrar.
"""

from flask import request, jsonify, current_app
from app.collections import collections_bp
from app.collections.services import CollectionsService
from app.core.odoo import OdooRepository
from app import cache


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


@collections_bp.route('/report/account12', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def report_account12():
    """
    Endpoint para reporte general de cuentas por cobrar (Cuenta 12).
    """
    try:
        # Obtener parámetros de query
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        cutoff_date = request.args.get('date_cutoff')
        include_reconciled = request.args.get('include_reconciled') == 'true'
        summary_only = request.args.get('summary_only') == 'true'
        if cutoff_date:
            include_reconciled = True
        limit = request.args.get('limit', type=int, default=10000)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)

        # OPTIMIZACIÓN: Si es solo resumen y no hay fecha de corte, usar read_group
        if summary_only and not cutoff_date:
            summary = collections_service.get_report_summary(
                start_date=date_from,
                end_date=date_to,
                customer=customer,
                account_codes=account_codes,
                sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id,
                include_reconciled=include_reconciled
            )
            if summary:
                filters_applied = {
                    'date_from': date_from,
                    'date_to': date_to,
                    'customer': customer,
                    'account_codes': account_codes,
                    'sales_channel_id': sales_channel_id,
                    'doc_type_id': doc_type_id,
                    'date_cutoff': cutoff_date,
                    'include_reconciled': include_reconciled,
                    'summary_only': summary_only,
                    'limit': limit
                }
                return jsonify({
                    'success': True,
                    'data': [],
                    'count': 0,
                    'summary': summary,
                    'filters': filters_applied,
                    'message': 'Resumen optimizado generado exitosamente'
                }), 200
        
        # Obtener datos (método tradicional si es necesario)
        data = collections_service.get_report_lines(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            limit=limit,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id,
            cutoff_date=cutoff_date,
            include_reconciled=include_reconciled
        )

        def _summarize(rows):
            overall = {
                'debit': 0.0,
                'credit': 0.0,
                'pending_cutoff': 0.0,
                'paid_after_cutoff': 0.0,
                'saldo': 0.0,
                'overdue_amount': 0.0,
                'count': 0
            }
            accounts = {}
            for row in rows:
                acc = row.get('account_id/code') or 'N/A'
                acc_name = row.get('account_id/name') or ''
                debit = float(row.get('debit', 0.0) or 0.0)
                credit = float(row.get('credit', 0.0) or 0.0)
                # Saldo es amount_residual_with_retention (en soles)
                pending = float(row.get('amount_residual_with_retention', 0.0) or 0.0)
                # O si es histórico, usar amount_residual_historical
                if cutoff_date:
                    pending = float(row.get('amount_residual_historical', 0.0) or 0.0)
                
                paid_after = float(row.get('paid_after_cutoff', 0.0) or 0.0)
                dias_vencido = int(row.get('dias_vencido', 0) or 0)

                overall['debit'] += debit
                overall['credit'] += credit
                overall['pending_cutoff'] += pending
                overall['paid_after_cutoff'] += paid_after
                overall['count'] += 1
                if dias_vencido > 0:
                    overall['overdue_amount'] += pending

                if acc not in accounts:
                    accounts[acc] = {
                        'account_code': acc,
                        'account_name': acc_name,
                        'debit': 0.0,
                        'credit': 0.0,
                        'pending_cutoff': 0.0,
                        'paid_after_cutoff': 0.0,
                        'saldo': 0.0,
                        'overdue_amount': 0.0,
                        'count': 0
                    }
                accounts[acc]['debit'] += debit
                accounts[acc]['credit'] += credit
                accounts[acc]['pending_cutoff'] += pending
                accounts[acc]['paid_after_cutoff'] += paid_after
                accounts[acc]['count'] += 1
                if dias_vencido > 0:
                    accounts[acc]['overdue_amount'] += pending

            for acc_code, acc_data in accounts.items():
                acc_data['saldo'] = acc_data['debit'] - acc_data['credit']
            overall['saldo'] = overall['debit'] - overall['credit']

            by_account = list(accounts.values())
            by_account.sort(key=lambda x: x['account_code'])
            return {
                'overall': overall,
                'by_account': by_account
            }

        summary = _summarize(data)
        
        # Preparar filtros aplicados para la respuesta
        filters_applied = {
            'date_from': date_from,
            'date_to': date_to,
            'customer': customer,
            'account_codes': account_codes,
            'sales_channel_id': sales_channel_id,
            'doc_type_id': doc_type_id,
            'date_cutoff': cutoff_date,
            'include_reconciled': include_reconciled,
            'summary_only': summary_only,
            'limit': limit
        }
        
        return jsonify({
            'success': True,
            'data': [] if summary_only else data,
            'count': 0 if summary_only else len(data),
            'summary': summary,
            'filters': filters_applied,
            'message': f'Reporte generado exitosamente con {len(data)} registros'
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
            'message': f'Error al generar reporte: {str(e)}',
            'data': []
        }), 500


@collections_bp.route('/report/national', methods=['GET'])
def report_national():
    """
    Endpoint para reporte de cuentas por cobrar NACIONALES.
    
    Aplica filtro para mostrar solo ventas nacionales (Perú).
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial (formato: YYYY-MM-DD)
        - date_to (str, optional): Fecha final (formato: YYYY-MM-DD)
        - customer (str, optional): Nombre del cliente a filtrar
        - account_codes (str, optional): Códigos de cuenta separados por coma
        - limit (int, optional): Límite de registros (default: 10000)
    
    Response (JSON):
        {
            "success": true,
            "data": [...],
            "count": 123,
            "filters": {...},
            "filter_type": "nacional"
        }
    """
    try:
        # Obtener parámetros de query
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes')
        limit = request.args.get('limit', type=int, default=10000)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener datos generales
        all_data = collections_service.get_report_lines(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            limit=limit,
            account_codes=account_codes
        )
        
        # Aplicar filtro nacional
        data = collections_service.filter_nacional(all_data)
        
        # Preparar filtros aplicados para la respuesta
        filters_applied = {
            'date_from': date_from,
            'date_to': date_to,
            'customer': customer,
            'account_codes': account_codes,
            'limit': limit,
            'filter_type': 'nacional'
        }
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'total_before_filter': len(all_data),
            'filters': filters_applied,
            'message': f'Reporte nacional generado con {len(data)} registros de {len(all_data)} totales'
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
            'message': f'Error al generar reporte nacional: {str(e)}',
            'data': []
        }), 500


@collections_bp.route('/report/international', methods=['GET'])
def report_international():
    """
    Endpoint para reporte de cuentas por cobrar INTERNACIONALES.
    
    Incluye cálculos de mora, días de vencimiento y antigüedad.
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial (formato: YYYY-MM-DD)
        - date_to (str, optional): Fecha final (formato: YYYY-MM-DD)
        - customer (str, optional): Nombre del cliente a filtrar
        - payment_state (str, optional): Estado de pago
        - limit (int, optional): Límite de registros (default: 10000)
    
    Response (JSON):
        {
            "success": true,
            "data": [...],  # Incluye campos calculados: dias_vencido, monto_interes, estado_deuda, antiguedad
            "count": 123,
            "filters": {...},
            "filter_type": "internacional"
        }
    """
    try:
        # Obtener parámetros de query
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        payment_state = request.args.get('payment_state')
        limit = request.args.get('limit', type=int, default=10000)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener datos internacionales con cálculos
        data = collections_service.get_report_internacional(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            payment_state=payment_state,
            limit=limit
        )
        
        # Preparar filtros aplicados para la respuesta
        filters_applied = {
            'date_from': date_from,
            'date_to': date_to,
            'customer': customer,
            'payment_state': payment_state,
            'limit': limit,
            'filter_type': 'internacional'
        }
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
            'filters': filters_applied,
            'message': f'Reporte internacional generado con {len(data)} registros'
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
            'message': f'Error al generar reporte internacional: {str(e)}',
            'data': []
        }), 500


@collections_bp.route('/filter-options', methods=['GET'])
def filter_options():
    """
    Endpoint para obtener las opciones de filtros (canales de venta, tipos de documento).
    
    Response (JSON):
        {
            "success": true,
            "data": {
                "sales_channels": [...],
                "document_types": [...]
            }
        }
    """
    try:
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener opciones de filtros
        filter_data = collections_service.get_filter_options()
        
        return jsonify({
            'success': True,
            'data': filter_data,
            'message': 'Opciones de filtros obtenidas exitosamente'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener opciones de filtros: {str(e)}',
            'data': {'sales_channels': [], 'document_types': []}
        }), 500


@collections_bp.route('/report/account12/rows', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def report_account12_rows():
    """
    Endpoint legacy de lazy loading HTML (deprecado).
    """
    return jsonify({
        'success': False,
        'message': 'Endpoint deprecado. Use /api/v1/collections/report/account12 (JSON).',
        'deprecated': True
    }), 410


@collections_bp.route('/report/account12/stats', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def report_account12_stats():
    """
    Endpoint para obtener KPIs agregados sin traer filas.
    """
    try:
        print(f"[DEBUG] report_account12_stats llamado")
        
        # Obtener filtros (mismos que rows)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes', '122,1212,123,1312,132,13')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        cutoff_date = request.args.get('date_cutoff')
        include_reconciled = request.args.get('include_reconciled') == 'true'
        if cutoff_date:
            include_reconciled = True
        
        # Crear servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener datos (método tradicional para asegurar exactitud)
        data = collections_service.get_report_lines(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            limit=50000, # Límite alto para stats
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id,
            cutoff_date=cutoff_date,
            include_reconciled=include_reconciled
        )

        total_amount = 0.0
        pending_amount = 0.0
        overdue_amount = 0.0
        
        for row in data:
            debit = float(row.get('debit', 0.0) or 0.0)
            credit = float(row.get('credit', 0.0) or 0.0)
            total_amount += (debit - credit)
            
            pending = float(row.get('amount_residual_with_retention', 0.0) or 0.0)
            if cutoff_date:
                pending = float(row.get('amount_residual_historical', 0.0) or 0.0)
            
            pending_amount += pending
            if int(row.get('dias_vencido', 0) or 0) > 0:
                overdue_amount += pending

        stats = {
            'total_count': len(data),
            'total_amount': round(total_amount, 2),
            'pending_amount': round(pending_amount, 2),
            'overdue_amount': round(overdue_amount, 2),
            'paid_amount': round(total_amount - pending_amount, 2)
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Stats calculados exitosamente'
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error calculando stats: {str(e)}',
            'data': {
                'total_count': 0,
                'total_amount': 0.0,
                'pending_amount': 0.0,
                'overdue_amount': 0.0,
                'paid_amount': 0.0
            }
        }), 200


@collections_bp.route('/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado del módulo de cobranzas.
    
    Response (JSON):
        {
            "module": "collections",
            "status": "active",
            "endpoints": [...]
        }
    """
    return jsonify({
        'module': 'collections',
        'status': 'active',
        'endpoints': [
            '/report/account12',
            '/report/national',
            '/report/international',
            '/filter-options',
            '/status'
        ]
    }), 200

