# -*- coding: utf-8 -*-
"""
Rutas de Cobranzas (Collections).

Endpoints para reportes de cuentas por cobrar.
"""

from flask import request, jsonify, current_app
from app.collections import collections_bp
from app.collections.services import CollectionsService
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


@collections_bp.route('/report/account12', methods=['GET'])
def report_account12():
    """
    Endpoint para reporte general de cuentas por cobrar (Cuenta 12).
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial (formato: YYYY-MM-DD)
        - date_to (str, optional): Fecha final (formato: YYYY-MM-DD)
        - customer (str, optional): Nombre del cliente a filtrar
        - account_codes (str, optional): Códigos de cuenta separados por coma
        - sales_channel_id (int, optional): ID del canal de ventas
        - doc_type_id (int, optional): ID del tipo de documento
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
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        limit = request.args.get('limit', type=int, default=10000)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener datos
        data = collections_service.get_report_lines(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            limit=limit,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id
        )
        
        # Preparar filtros aplicados para la respuesta
        filters_applied = {
            'date_from': date_from,
            'date_to': date_to,
            'customer': customer,
            'account_codes': account_codes,
            'sales_channel_id': sales_channel_id,
            'doc_type_id': doc_type_id,
            'limit': limit
        }
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data),
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

