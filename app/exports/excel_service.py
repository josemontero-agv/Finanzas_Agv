# -*- coding: utf-8 -*-
"""
Servicio de Exportación a Excel.

Genera archivos Excel a partir de datos de reportes.
"""

from io import BytesIO
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


class ExcelExportService:
    """
    Servicio para exportar datos a archivos Excel con formato profesional.
    """
    
    # Estilos predefinidos
    HEADER_FILL = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    HEADER_ALIGNMENT = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    CELL_BORDER = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    @staticmethod
    def export_collections_report(data, filename="reporte_cobranzas.xlsx"):
        """
        Exporta reporte de cobranzas a Excel con todas las columnas.
        Formato simplificado y profesional similar al reporte de tesorería.
        
        Args:
            data (list): Lista de diccionarios con datos del reporte
            filename (str): Nombre del archivo a generar
        
        Returns:
            BytesIO: Buffer con el archivo Excel generado
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "CxC - Cuenta 12"
        
        # Definir columnas alineadas con el nuevo mapeo de cobranzas
        # Cada entrada acepta una llave o varias llaves fallback.
        columns = [
            (('account.move/l10n_latam_document_type_id', 'l10n_latam_document_type_id'), 'Tipo Documento'),
            (('account.move/name', 'move_name'), 'Nro Factura'),
            (('account.move/invoice_origin', 'invoice_origin'), 'Nro Pedido'),
            (('move_id/invoice_date', 'invoice_date'), 'Fecha Factura'),
            (('account.move/invoice_date', 'date'), 'Fecha Contabilización'),
            (('account.move/invoice_date_due', 'invoice_date_due', 'date_maturity'), 'Fecha Vencimiento'),
            (('account.move/l10n_latam_boe_number', 'l10n_latam_boe_number'), 'Letra'),
            (('account_id/code',), 'Cuenta'),
            (('account_id/name',), 'Nombre Cuenta'),
            (('patner_id/vat', 'partner_vat'), 'RUC/DNI'),
            (('patner_id', 'partner_name'), 'Cliente'),
            (('account_id/currency_id', 'currency_id'), 'Moneda'),
            (('account.move/amount_total', 'amount_total', 'amount_currency'), 'Monto Total'),
            (('account.move/amount_residual', 'amount_residual_with_retention', 'amount_residual_historical'), 'Saldo'),
            (('debit',), 'Débito'),
            (('credit',), 'Haber'),
            (('amount_residual_historical',), 'Pendiente al corte'),
            (('paid_after_cutoff',), 'Pagado después corte'),
            (('dias_vencido',), 'Días Vencido'),
            (('estado_deuda',), 'Estado'),
            (('antiguedad',), 'Antigüedad'),
            (('account.move/invoice_payment_term_id', 'invoice_payment_term_id'), 'Condición Pago'),
            (('account.move.line/name', 'name'), 'Descripción'),
            (('account.move/invoice_user_id', 'invoice_user_name', 'move_id/invoice_user_id'), 'Vendedor'),
            (('account.move/linea_comercial', 'linea_comercial', 'team_name'), 'Línea Comercial'),
            (('grupo_comercial', 'agr.credit.customer/partner_groups_ids', 'agr.credit.customer/patner_groups_ids', 'partner_groups'), 'Grupo Comercial'),
            (('agr.credit.customer/sub_channel_id', 'sub_channel_id'), 'Sub Canal'),
            (('account.move/sales_channel_id', 'sales_channel_name', 'move_id/sales_channel_id'), 'Canal de Venta'),
            (('account.move/sale_type_id', 'account.move/sales_type_id', 'sales_type_name', 'move_id/sales_type_id'), 'Tipo de Venta'),
            (('patner_id/state_id', 'partner_state'), 'Provincia'),
            (('patner_id/country_id', 'partner_country_name'), 'País'),
        ]

        def get_value(record, key_candidates):
            for key in key_candidates:
                value = record.get(key)
                if value is not None and value != '' and value is not False:
                    return value
            return ''

        def format_date_for_export(value):
            if isinstance(value, str) and len(value) == 10 and value[4] == '-' and value[7] == '-':
                yyyy, mm, dd = value.split('-')
                return f"{dd}/{mm}/{yyyy}"
            return value
        
        # Escribir encabezados
        for col_num, (_keys, header) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = ExcelExportService.HEADER_FILL
            cell.font = ExcelExportService.HEADER_FONT
            cell.alignment = ExcelExportService.HEADER_ALIGNMENT
            cell.border = ExcelExportService.CELL_BORDER
        
        # Escribir datos
        for row_num, record in enumerate(data, 2):
            for col_num, (keys, _header) in enumerate(columns, 1):
                key_candidates = keys if isinstance(keys, tuple) else (keys,)
                value = get_value(record, key_candidates)
                
                # Convertir valores Many2One (listas) a string
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    value = str(value[1])  # Extraer el nombre
                elif isinstance(value, (list, tuple)):
                    value = str(value[0]) if value else ''
                
                # Convertir None a cadena vacía
                if value is None:
                    value = ''
                
                # Formatear valores numéricos
                numeric_keys = {
                    'amount_currency', 'amount_residual_with_retention', 'amount_residual_signed',
                    'amount_total', 'account.move/amount_total', 'account.move/amount_residual',
                    'debit', 'credit', 'amount_residual_historical', 'paid_after_cutoff', 'dias_vencido'
                }
                if any(k in numeric_keys for k in key_candidates):
                    try:
                        value = float(value) if value else 0
                        if 'dias_vencido' in key_candidates:
                            value = int(value)
                    except:
                        value = 0
                else:
                    # Formato de fecha solicitado: dd/mm/aaaa
                    value = format_date_for_export(value)
                
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.border = ExcelExportService.CELL_BORDER
                
                # Formato especial para números
                if any(k in {
                    'amount_currency', 'amount_residual_with_retention', 'amount_residual_signed',
                    'amount_total', 'account.move/amount_total', 'account.move/amount_residual',
                    'debit', 'credit', 'amount_residual_historical', 'paid_after_cutoff'
                } for k in key_candidates):
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal='right')
                elif 'dias_vencido' in key_candidates:
                    cell.alignment = Alignment(horizontal='center')
                    # Resaltar en rojo si está vencido
                    if value > 0:
                        cell.font = Font(color="FF0000", bold=True)
                elif 'estado_deuda' in key_candidates:
                    cell.alignment = Alignment(horizontal='center')
                    # Color de fondo según estado
                    if value == 'VENCIDO':
                        cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
                    else:
                        cell.fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        
        # Ajustar anchos de columna según contenido
        column_widths = {
            1: 18, 2: 18, 3: 16, 4: 14, 5: 18, 6: 16, 7: 12, 8: 12, 9: 28, 10: 14,
            11: 28, 12: 10, 13: 16, 14: 16, 15: 12, 16: 12, 17: 18, 18: 18, 19: 12,
            20: 12, 21: 14, 22: 22, 23: 32, 24: 24, 25: 24, 26: 24, 27: 16, 28: 20,
            29: 20, 30: 20, 31: 18
        }
        
        for col_num, width in column_widths.items():
            ws.column_dimensions[get_column_letter(col_num)].width = width
        
        # Guardar en buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def export_treasury_report(data, filename="reporte_tesoreria.xlsx"):
        """
        Exporta reporte de tesorería (CxP) a Excel con todos los campos expandidos.
        Formato similar al reporte de collections.
        
        Args:
            data (list): Lista de diccionarios con datos del reporte
            filename (str): Nombre del archivo a generar
        
        Returns:
            BytesIO: Buffer con el archivo Excel generado
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "CxP - Cuenta 42"
        
        # Definir columnas expandidas (incluye históricos y débitos/hábers)
        columns = [
            ('invoice_date', 'Fecha Factura'),
            ('date', 'Fecha Contabilización'),
            ('l10n_latam_document_type_id', 'Tipo Documento'),
            ('move_name', 'Número Documento'),
            ('l10n_latam_boe_number', 'Número Letra'),
            ('ref', 'Referencia'),
            ('invoice_origin', 'Origen'),
            ('account_code', 'Cuenta'),
            ('account_name', 'Nombre Cuenta'),
            ('supplier_vat', 'RUC Proveedor'),
            ('supplier_name', 'Proveedor'),
            ('supplier_country', 'País'),
            ('supplier_state', 'Provincia'),
            ('supplier_city', 'Ciudad'),
            ('supplier_email', 'Email'),
            ('currency_id', 'Moneda'),
            ('amount_total_in_currency_signed', 'Total Origen'),
            ('amount_residual_with_retention', 'Adeudado Origen'),
            ('amount_total_signed', 'Total S/.'),
            ('debit', 'Débito'),
            ('credit', 'Haber'),
            ('amount_residual_historical', 'Pendiente al corte'),
            ('paid_after_cutoff', 'Pagado después corte'),
            ('invoice_date_due', 'Fecha Vencimiento'),
            ('dias_vencido', 'Días Vencido'),
            ('estado_deuda', 'Estado'),
            ('antiguedad', 'Antigüedad'),
            ('invoice_payment_term_id', 'Condición Pago'),
            ('payment_state', 'Estado Pago'),
            ('state', 'Estado Factura'),
            ('invoice_user_id', 'Usuario Responsable'),
            ('name', 'Descripción'),
        ]
        
        # Escribir encabezados
        for col_num, (key, header) in enumerate(columns, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.fill = ExcelExportService.HEADER_FILL
            cell.font = ExcelExportService.HEADER_FONT
            cell.alignment = ExcelExportService.HEADER_ALIGNMENT
            cell.border = ExcelExportService.CELL_BORDER
        
        # Escribir datos
        for row_num, record in enumerate(data, 2):
            for col_num, (key, header) in enumerate(columns, 1):
                value = record.get(key, '')
                
                # Convertir valores Many2One (listas) a string
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    value = str(value[1])  # Extraer el nombre
                elif isinstance(value, (list, tuple)):
                    value = str(value[0]) if value else ''
                
                # Convertir None a cadena vacía
                if value is None:
                    value = ''
                
                # Formatear valores numéricos
                if key in ['amount_total_in_currency_signed', 'amount_residual_with_retention', 'amount_total_signed', 'debit', 'credit', 'amount_residual_historical', 'paid_after_cutoff', 'dias_vencido']:
                    try:
                        value = float(value) if value else 0
                        if key == 'dias_vencido':
                            value = int(value)
                    except:
                        value = 0
                
                cell = ws.cell(row=row_num, column=col_num, value=value)
                cell.border = ExcelExportService.CELL_BORDER
                
                # Formato especial para números
                if key in ['amount_total_in_currency_signed', 'amount_residual_with_retention', 'amount_total_signed', 'debit', 'credit', 'amount_residual_historical', 'paid_after_cutoff']:
                    cell.number_format = '#,##0.00'
                    cell.alignment = Alignment(horizontal='right')
                elif key == 'dias_vencido':
                    cell.alignment = Alignment(horizontal='center')
                    # Resaltar en rojo si está vencido
                    if value > 0:
                        cell.font = Font(color="FF0000", bold=True)
                elif key == 'estado_deuda':
                    cell.alignment = Alignment(horizontal='center')
                    # Color de fondo según estado
                    if value == 'VENCIDO':
                        cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
                    else:
                        cell.fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        
        # Ajustar anchos de columna
        column_widths = [12, 14, 14, 16, 14, 12, 10, 25, 14, 30, 12, 18, 18, 18, 16, 25, 10, 18, 18, 18, 14, 12, 12, 20, 18, 14, 14, 20, 30]
        for col, width in enumerate(column_widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Guardar en buffer
        buffer = BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        
        return buffer

