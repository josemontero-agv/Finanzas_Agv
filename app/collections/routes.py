# -*- coding: utf-8 -*-
"""
Rutas de Cobranzas (Collections).

Endpoints para reportes de cuentas por cobrar.
"""

from flask import request, jsonify, current_app, render_template
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


@collections_bp.route('/report/account12/rows', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def report_account12_rows():
    """
    Endpoint para lazy loading con HTMX - retorna solo filas HTML.
    VERSIÓN OPTIMIZADA con paginación real en Odoo.
    """
    try:
        print(f"[DEBUG] report_account12_rows llamado - page={request.args.get('page', 1)}")
        # Parámetros de paginación
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        # Filtros
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes', '122,1212,123,1312,132')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        
        # Crear repositorio y servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # ✅ OBTENER DATOS PAGINADOS (solo esta página)
        try:
            result = collections_service.get_report_lines_paginated(
                page=page,
                per_page=per_page,
                start_date=date_from,
                end_date=date_to,
                customer=customer,
                account_codes=account_codes,
                sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id
            )
            
            data = result['data']
            has_more = result.get('has_more', False)
            total_count = result.get('total_count', 0)
            print(f"[DEBUG] Página {page}: {len(data)} filas, total={total_count}, has_more={has_more}")
        except Exception as pagination_error:
            print(f"[ERROR] Error en paginación optimizada: {pagination_error}")
            import traceback
            traceback.print_exc()
            # Fallback: usar método original
            print("[WARN] Usando método original como fallback")
            all_data = collections_service.get_report_lines(
                start_date=date_from,
                end_date=date_to,
                customer=customer,
                account_codes=account_codes,
                sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id,
                limit=0
            )
            # Paginar en memoria como fallback
            start = (page - 1) * per_page
            end = start + per_page
            data = all_data[start:end]
            has_more = len(all_data) > end
            total_count = len(all_data)
            print(f"[DEBUG] Fallback - Página {page}: {len(data)} filas, total={total_count}, has_more={has_more}")
        
        # Si no hay datos
        if not data and page == 1:
            return '''
                <tr>
                    <td colspan="33" class="text-center py-4 text-gray-500">
                        No se encontraron registros con los filtros aplicados
                    </td>
                </tr>
            '''
        elif not data:
            # Página sin datos - eliminar trigger de scroll infinito
            return '''
                <div id="infinite-scroll-trigger" hx-swap-oob="delete"></div>
            '''
        
        print(f"[DEBUG] Datos obtenidos: {len(data)} filas, has_more={has_more}")
        
        # Renderizar filas
        html = render_template('collections/report_account12_rows.html', rows=data)
        
        print(f"[DEBUG] HTML renderizado: {len(html)} caracteres, has_more={has_more}")
        
        # Para fetch/axios: retornar solo las filas HTML
        # El frontend manejará el scroll infinito con Intersection Observer
        # Si no hay más páginas, agregar un comentario que el frontend puede detectar
        if not has_more:
            html += '<!-- NO_MORE_DATA -->'
        
        return html
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f'''
            <tr>
                <td colspan="33" class="text-center text-red-600 py-4">
                    Error: {str(e)}
                </td>
            </tr>
        ''', 500


@collections_bp.route('/report/account12/stats', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def report_account12_stats():
    """
    Endpoint para obtener KPIs agregados sin traer filas.
    Optimizado con consultas agregadas en Odoo.
    
    Query Parameters:
        - date_from (str, optional): Fecha inicial (formato: YYYY-MM-DD)
        - date_to (str, optional): Fecha final (formato: YYYY-MM-DD)
        - customer (str, optional): Nombre del cliente a filtrar
        - account_codes (str, optional): Códigos de cuenta separados por coma
        - sales_channel_id (int, optional): ID del canal de ventas
        - doc_type_id (int, optional): ID del tipo de documento
    
    Response (JSON):
        {
            "success": true,
            "data": {
                "total_count": 1234,
                "total_amount": 500000.00,
                "pending_amount": 250000.00,
                "overdue_amount": 50000.00,
                "paid_amount": 250000.00
            }
        }
    """
    try:
        print(f"[DEBUG] report_account12_stats llamado")
        
        # Obtener filtros (mismos que rows)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes', '122,1212,123,1312,132')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        
        print(f"[DEBUG] Filtros recibidos: date_from={date_from}, date_to={date_to}, customer={customer}, account_codes={account_codes}, sales_channel_id={sales_channel_id}, doc_type_id={doc_type_id}")
        
        # Crear servicio
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
        # Obtener stats agregados
        stats = collections_service.get_aggregated_stats(
            start_date=date_from,
            end_date=date_to,
            customer=customer,
            account_codes=account_codes,
            sales_channel_id=sales_channel_id,
            doc_type_id=doc_type_id
        )
        
        print(f"[DEBUG] Stats calculados: {stats}")
        
        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Stats calculados exitosamente'
        }), 200
        
    except Exception as e:
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

