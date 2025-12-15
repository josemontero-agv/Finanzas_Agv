# -*- coding: utf-8 -*-
"""
Rutas de Exportación.

Endpoints para exportar reportes a diferentes formatos.
"""

from flask import request, send_file, jsonify, current_app
from app.exports import exports_bp
from app.exports.excel_service import ExcelExportService
from app.collections.services import CollectionsService
from app.treasury.services import TreasuryService
from app.core.odoo import OdooRepository


def _get_odoo_repository():
    """Helper para crear instancia de OdooRepository."""
    try:
        return OdooRepository(
            url=current_app.config['ODOO_URL'],
            db=current_app.config['ODOO_DB'],
            username=current_app.config['ODOO_USER'],
            password=current_app.config['ODOO_PASSWORD']
        )
    except ValueError as e:
        raise ValueError(f"Error de configuración de Odoo: {str(e)}")


@exports_bp.route('/collections/excel', methods=['GET'])
def export_collections_excel():
    """
    Exporta reporte de cobranzas a Excel.
    
    Query Parameters:
        - date_from, date_to, customer, account_codes, sales_channel_id, doc_type_id, limit
    
    Response:
        Archivo Excel descargable
    """
    try:
        # Obtener parámetros (similares al reporte)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        customer = request.args.get('customer')
        account_codes = request.args.get('account_codes')
        sales_channel_id = request.args.get('sales_channel_id', type=int)
        doc_type_id = request.args.get('doc_type_id', type=int)
        limit = request.args.get('limit', type=int, default=10000)
        cutoff_date = request.args.get('date_cutoff')
        include_reconciled = request.args.get('include_reconciled') == 'true'
        if cutoff_date:
            include_reconciled = True
        
        # Obtener datos
        odoo_repo = _get_odoo_repository()
        collections_service = CollectionsService(odoo_repo)
        
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
        
        # Generar Excel
        excel_buffer = ExcelExportService.export_collections_report(data)
        
        # Generar nombre de archivo con timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filters_suffix = ""
        if cutoff_date:
            filters_suffix = f"_corte_{cutoff_date}"
        elif date_from or date_to:
            filters_suffix = f"_{date_from or 'inicio'}_{date_to or 'hoy'}"
        
        filename = f"reporte_cxc_general{filters_suffix}_{timestamp}.xlsx"
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al exportar a Excel: {str(e)}'
        }), 500


@exports_bp.route('/treasury/excel', methods=['GET'])
def export_treasury_excel():
    """
    Exporta reporte de tesorería a Excel.
    
    Query Parameters:
        - date_from, date_to, date_cutoff, supplier, etc.
    
    Response:
        Archivo Excel descargable
    """
    try:
        # Obtener parámetros
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        date_cutoff = request.args.get('date_cutoff') # Nuevo parámetro
        supplier = request.args.get('supplier')
        account_codes = request.args.get('account_codes')
        payment_state = request.args.get('payment_state')
        doc_type_id = request.args.get('doc_type_id', type=int)
        reference = request.args.get('reference')
        has_retention = request.args.get('has_retention') == 'true'
        has_origin = request.args.get('has_origin') == 'true'
        include_reconciled = request.args.get('include_reconciled') == 'true'
        limit = request.args.get('limit', type=int, default=10000)

        # En corte histórico incluir conciliados para cuadrar con el mayor (misma lógica que /treasury/report/account42)
        if date_cutoff:
            include_reconciled = True
        
        # Obtener datos
        odoo_repo = _get_odoo_repository()
        treasury_service = TreasuryService(odoo_repo)
        
        data = treasury_service.get_accounts_payable_report(
            start_date=date_from,
            end_date=date_to,
            cutoff_date=date_cutoff, # Pasando el parámetro
            supplier=supplier,
            limit=limit,
            account_codes=account_codes,
            payment_state=payment_state,
            doc_type_id=doc_type_id,
            reference=reference,
            has_retention=has_retention,
            has_origin=has_origin,
            include_reconciled=include_reconciled
        )
        
        # Generar Excel
        excel_buffer = ExcelExportService.export_treasury_report(data)
        
        # Generar nombre de archivo
        suffix = ""
        if date_cutoff:
            suffix = f"_corte_{date_cutoff}"
        else:
            suffix = f"_{date_from or 'inicio'}_{date_to or 'hoy'}"
            
        filename = f"reporte_tesoreria{suffix}.xlsx"
        
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al exportar a Excel: {str(e)}'
        }), 500

