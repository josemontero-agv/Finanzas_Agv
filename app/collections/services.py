# -*- coding: utf-8 -*-
"""
Servicio de Cobranzas (Collections).

Lógica de negocio para reportes de cuentas por cobrar.
Migrado desde dashboard-Cobranzas/services/report_service.py
"""

from datetime import datetime
from app.core.calculators import calcular_mora, calcular_dias_vencido, clasificar_antiguedad


class CollectionsService:
    """
    Servicio para generar reportes de cuentas por cobrar.
    """
    
    def __init__(self, odoo_repository):
        """
        Inicializa el servicio de reportes.
        
        Args:
            odoo_repository (OdooRepository): Instancia del repositorio de Odoo
        """
        self.repository = odoo_repository
    
    # Funciones de filtro integradas
    @staticmethod
    def filter_internacional(sales_lines):
        """
        Filtra líneas que corresponden a VENTA INTERNACIONAL.
        
        Incluye líneas donde:
        - La línea comercial contiene "VENTA INTERNACIONAL" o "INTERNACIONAL"
        - El canal de venta contiene "INTERNACIONAL"
        - El país no es PE
        
        Args:
            sales_lines (list): Lista de líneas de venta/cobranza
        
        Returns:
            list: Líneas filtradas que son internacionales
        """
        internacional_lines = []
        
        for line in sales_lines:
            is_internacional = False
            
            # Verificar línea comercial
            linea_comercial = line.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea = str(linea_comercial[1]).upper()
                if 'VENTA INTERNACIONAL' in nombre_linea or 'INTERNACIONAL' in nombre_linea:
                    is_internacional = True
            
            # Verificar canal de ventas
            canal_ventas = line.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = str(canal_ventas[1]).upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    is_internacional = True
            
            # Verificar país (si no es PE, es internacional)
            country_code = line.get('country_code') or line.get('patner_id/country_code')
            if country_code and country_code != 'PE':
                is_internacional = True
            
            if is_internacional:
                internacional_lines.append(line)
        
        return internacional_lines
    
    @staticmethod
    def filter_nacional(sales_lines):
        """
        Filtra líneas que corresponden a VENTA NACIONAL (Perú).
        
        Excluye líneas donde:
        - La línea comercial contiene "VENTA INTERNACIONAL" o "INTERNACIONAL"
        - El canal de venta contiene "INTERNACIONAL"
        - El país no es PE
        
        Args:
            sales_lines (list): Lista de líneas de venta/cobranza
        
        Returns:
            list: Líneas filtradas que son nacionales
        """
        nacional_lines = []
        
        for line in sales_lines:
            is_internacional = False
            
            # Verificar línea comercial
            linea_comercial = line.get('commercial_line_national_id')
            if linea_comercial and isinstance(linea_comercial, list) and len(linea_comercial) > 1:
                nombre_linea = str(linea_comercial[1]).upper()
                if 'VENTA INTERNACIONAL' in nombre_linea or 'INTERNACIONAL' in nombre_linea:
                    is_internacional = True
            
            # Verificar canal de ventas
            canal_ventas = line.get('sales_channel_id')
            if canal_ventas and isinstance(canal_ventas, list) and len(canal_ventas) > 1:
                nombre_canal = str(canal_ventas[1]).upper()
                if 'VENTA INTERNACIONAL' in nombre_canal or 'INTERNACIONAL' in nombre_canal:
                    is_internacional = True
            
            # Si no es internacional, es nacional
            if not is_internacional:
                nacional_lines.append(line)
        
        return nacional_lines
    
    def get_report_lines(self, start_date=None, end_date=None, customer=None, limit=0,
                         account_codes=None, sales_channel_id=None, doc_type_id=None):
        """
        Obtener líneas de reporte de CxC siguiendo la cadena de relaciones.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
            customer (str): Nombre de cliente a filtrar
            limit (int): Límite de registros
            account_codes (str): Códigos de cuenta separados por coma
            sales_channel_id (int): ID del canal de ventas
            doc_type_id (int): ID del tipo de documento
        
        Returns:
            list: Líneas de reporte CxC
        """
        try:
            print("[INFO] Obteniendo líneas de reporte CxC...")
            
            if not self.repository.is_connected():
                print("[ERROR] No hay conexión a Odoo disponible")
                return []
            
            # Códigos de cuenta a buscar - Específicamente para CxC General
            if account_codes:
                codes = [c.strip() for c in account_codes.split(',') if c.strip()]
            else:
                codes = ['122', '1212', '123', '1312', '132']  # Cuentas específicas CxC por defecto
            
            # Construir dominio base
            line_domain = [
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),  # False = pendientes por cobrar
                # Incluir facturas, notas de crédito y letras de cambio
                ('move_id.move_type', 'in', ['out_invoice', 'out_refund', 'out_bill']),
            ]
            
            # Construir OR para códigos de cuenta
            if len(codes) > 1:
                or_operators = ['|'] * (len(codes) - 1)
                code_conditions = []
                for code in codes:
                    code_conditions.append(('account_id.code', '=like', f'{code}%'))
                line_domain = or_operators + code_conditions + line_domain
            else:
                line_domain.insert(0, ('account_id.code', '=like', f'{codes[0]}%'))

            # Excluir cuenta específica de letras
            line_domain.append(('account_id.code', '!=', '1239001'))
            
            # Filtros adicionales
            if start_date:
                line_domain.append(('date', '>=', start_date))
            if end_date:
                line_domain.append(('date', '<=', end_date))
            if customer:
                line_domain.append(('partner_id.name', 'ilike', customer))
            if sales_channel_id:
                line_domain.append(('move_id.sales_channel_id', '=', sales_channel_id))
            if doc_type_id:
                line_domain.append(('move_id.l10n_latam_document_type_id', '=', doc_type_id))
            
            # Campos a extraer
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
            ]
            
            effective_limit = limit if limit and limit > 0 else 10000
            lines = self.repository.search_read(
                'account.move.line', line_domain, line_fields,
                limit=effective_limit
            )
            
            print(f"[OK] Obtenidas {len(lines)} líneas de asiento contable")
            
            if not lines:
                return []
            
            # Extraer IDs únicos
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            account_ids = list(set([l['account_id'][0] for l in lines if l.get('account_id')]))
            
            # Obtener datos de facturas
            move_map = {}
            if move_ids:
                move_fields = [
                    'id', 'name', 'payment_state', 'invoice_date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'amount_residual_with_retention', 'currency_id',
                    'l10n_latam_boe_number',
                    'ref', 'invoice_payment_term_id', 'invoice_user_id',
                    'sales_channel_id', 'sale_type_id',
                ]
                moves = self.repository.read('account.move', move_ids, move_fields)
                move_map = {m['id']: m for m in moves}
            
            # Obtener datos de clientes
            partner_map = {}
            partner_groups_map = {}
            partner_group_ids = set()
            if partner_ids:
                partner_fields = [
                    'id', 'name', 'vat', 'state_id', 'l10n_pe_district',
                    'country_code', 'country_id', 'groups_ids'
                ]
                partners = self.repository.read('res.partner', partner_ids, partner_fields)
                for partner in partners:
                    partner_map[partner['id']] = partner
                    for gid in partner.get('groups_ids') or []:
                        partner_group_ids.add(gid)

            group_name_map = {}
            if partner_group_ids:
                try:
                    group_records = self.repository.read(
                        'agr.groups',
                        list(partner_group_ids),
                        ['id', 'name']
                    )
                    group_name_map = {g['id']: g.get('name', '') for g in group_records}
                except Exception as e:
                    print(f"[WARN] No se pudieron obtener los nombres de grupos de cliente: {e}")

            if partner_map:
                for partner_id_key, partner_data in partner_map.items():
                    names = []
                    for gid in partner_data.get('groups_ids') or []:
                        group_name = group_name_map.get(gid)
                        if group_name:
                            names.append(group_name)
                    partner_groups_map[partner_id_key] = ', '.join(names)
            
            # Obtener datos de cuentas
            account_map = {}
            if account_ids:
                accounts = self.repository.read('account.account', account_ids, ['id', 'code', 'name'])
                account_map = {a['id']: a for a in accounts}
            
            # Obtener información de crédito (para Sub Canal)
            credit_map = {}
            if partner_ids:
                try:
                    credit_customers = self.repository.search_read(
                        'agr.credit.customer',
                        [('partner_id', 'in', partner_ids)],
                        ['partner_id', 'sub_channel_id']
                    )
                    credit_map = {cc['partner_id'][0]: cc for cc in credit_customers}
                except Exception as e:
                    print(f"[WARN] No se pudo obtener agr.credit.customer: {e}")

            # Combinar datos
            rows = []
            def m2o_name(val):
                if isinstance(val, list) and len(val) >= 2:
                    return val[1]
                return ''
            
            for line in lines:
                move_id = line['move_id'][0] if line.get('move_id') else None
                partner_id = line['partner_id'][0] if line.get('partner_id') else None
                account_id = line['account_id'][0] if line.get('account_id') else None
                
                move = move_map.get(move_id, {})
                partner = partner_map.get(partner_id, {})
                account = account_map.get(account_id, {})
                credit = credit_map.get(partner_id, {})
                
                # Determinar Sub Canal
                sub_channel_raw = m2o_name(credit.get('sub_channel_id'))
                country_code = partner.get('country_code', '')
                
                if not sub_channel_raw or sub_channel_raw == 'N/A' or sub_channel_raw.strip() == '':
                    if country_code == 'PE':
                        sub_channel_final = 'NACIONAL'
                    elif country_code and country_code != '':
                        sub_channel_final = 'INTERNACIONAL'
                    else:
                        sub_channel_final = 'N/A'
                else:
                    sub_channel_final = sub_channel_raw

                # Determinar grupos del partner
                partner_groups_display = partner_groups_map.get(partner_id, '')
                
                row = {
                    'payment_state': move.get('payment_state', ''),
                    'invoice_date': move.get('invoice_date', ''),
                    'I10nn_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'move_name': move.get('name', ''),
                    'invoice_origin': move.get('invoice_origin', ''),
                    'account_id/code': account.get('code', ''),
                    'account_id/name': account.get('name', ''),
                    'patner_id/vat': partner.get('vat', ''),
                    'patner_id': partner.get('name', ''),
                    'patner_id/state_id': m2o_name(partner.get('state_id')),
                    'patner_id/l10n_pe_district': partner.get('l10n_pe_district', ''),
                    'patner_id/country_code': country_code,
                    'patner_id/country_id': m2o_name(partner.get('country_id')),
                    'currency_id': m2o_name(line.get('currency_id') or move.get('currency_id')),
                    'amount_total': move.get('amount_total', 0.0),
                    'amount_residual_with_retention': move.get('amount_residual_with_retention', 0.0),
                    'amount_currency': line.get('amount_currency', 0.0),
                    'amount_residual_currency': line.get('amount_residual', 0.0),
                    'date': line.get('date', ''),
                    'date_maturity': line.get('date_maturity', ''),
                    'invoice_date_due': move.get('invoice_date_due', ''),
                    'ref': move.get('ref', ''),
                    'invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')),
                    'name': line.get('name', ''),
                    'move_id/invoice_user_id': m2o_name(move.get('invoice_user_id')),
                    'move_id/sales_channel_id': m2o_name(move.get('sales_channel_id')),
                    'move_id/sales_type_id': m2o_name(move.get('sale_type_id')),
                    'move_id/payment_state': move.get('payment_state', ''),
                    'partner_groups': partner_groups_display,
                    'sub_channel_id': sub_channel_final,
                }
                
                rows.append(row)
            
            print(f"[OK] Procesadas {len(rows)} líneas de CxC con TODOS los campos")
            return rows
            
        except Exception as e:
            print(f"[ERROR] Error al obtener las líneas de reporte CxC: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_report_internacional(self, start_date=None, end_date=None, customer=None, payment_state=None, limit=0):
        """
        Obtener reporte de facturas internacionales no pagadas con campos calculados.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
            customer (str): Nombre de cliente
            payment_state (str): Estado de pago
            limit (int): Límite de registros
        
        Returns:
            list: Líneas de reporte internacional con campos calculados
        """
        try:
            print("[INFO] Obteniendo reporte internacional...")
            
            if not self.repository.is_connected():
                print("[ERROR] No hay conexión a Odoo disponible")
                return []
            
            # Construir dominio
            line_domain = [
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),  # Solo no pagadas
                ('account_id.code', '=like', '12%'),
            ]
            
            if start_date:
                line_domain.append(('date', '>=', start_date))
            if end_date:
                line_domain.append(('date', '<=', end_date))
            if customer:
                line_domain.append(('partner_id.name', 'ilike', customer))
            
            # Campos a extraer (incluir amount_residual_with_retention)
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id', 'amount_residual_with_retention',
            ]
            
            lines = self.repository.search_read(
                'account.move.line', line_domain, line_fields,
                limit=limit if limit > 0 else 10000
            )
            
            if not lines:
                return []
            
            # Extraer IDs únicos
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            
            # Obtener facturas
            move_map = {}
            if move_ids:
                move_fields = [
                    'id', 'name', 'payment_state', 'invoice_date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'currency_id', 'invoice_payment_term_id',
                    'invoice_user_id', 'amount_total_signed', 'amount_residual_with_retention',
                ]
                moves = self.repository.read('account.move', move_ids, move_fields)
                move_map = {m['id']: m for m in moves}
                
                # Filtrar por payment_state si se especificó
                if payment_state:
                    move_map = {k: v for k, v in move_map.items() if v.get('payment_state') == payment_state}
            
            # Obtener clientes
            partner_map = {}
            if partner_ids:
                partner_fields = ['id', 'name', 'vat', 'country_code', 'country_id']
                partners = self.repository.read('res.partner', partner_ids, partner_fields)
                partner_map = {p['id']: p for p in partners}
            
            # Procesar y calcular campos
            rows = []
            today = datetime.today().date()
            
            def m2o_name(val):
                if isinstance(val, list) and len(val) >= 2:
                    return val[1]
                return ''
            
            for line in lines:
                move_id = line['move_id'][0] if line.get('move_id') else None
                partner_id = line['partner_id'][0] if line.get('partner_id') else None
                
                move = move_map.get(move_id, {})
                partner = partner_map.get(partner_id, {})
                
                # Crear estructura de línea temporal para filtro
                temp_line = {
                    'country_code': partner.get('country_code'),
                    'patner_id/country_code': partner.get('country_code'),
                }
                
                # Filtrar solo internacional
                internacional_lines = self.filter_internacional([temp_line])
                if not internacional_lines:
                    continue
                
                # Calcular campos
                invoice_date_due = move.get('invoice_date_due', '')
                amount_residual = move.get('amount_residual_with_retention', 0.0)
                
                # Días de vencido
                dias_vencido = calcular_dias_vencido(invoice_date_due, today) if invoice_date_due else 0
                
                # Monto de interés (12% anual, gracia 8 días)
                monto_interes = calcular_mora(dias_vencido, 0.12, amount_residual)
                
                # Estado de deuda
                estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'
                
                # Antigüedad
                antiguedad = clasificar_antiguedad(max(0, dias_vencido))
                
                row = {
                    'payment_state': move.get('payment_state', ''),
                    'vat': partner.get('vat', ''),
                    'patner_id': partner.get('name', ''),
                    'I10nn_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'name': move.get('name', ''),
                    'invoice_origin': move.get('invoice_origin', ''),
                    'invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')),
                    'invoice_date': move.get('invoice_date', ''),
                    'invoice_date_due': invoice_date_due,
                    'currency_id': m2o_name(move.get('currency_id')),
                    'amount_total_currency_signed': move.get('amount_total_currency_signed', move.get('amount_total', 0.0)),
                    'amount_residual_with_retention': amount_residual,
                    'monto_interes': monto_interes,
                    'dias_vencido': dias_vencido,
                    'estado_deuda': estado_deuda,
                    'antiguedad': antiguedad,
                    'invoice_user_id': m2o_name(move.get('invoice_user_id')),
                    'country_code': partner.get('country_code', ''),
                    'country_id': m2o_name(partner.get('country_id')),
                }
                
                rows.append(row)
            
            print(f"[OK] Procesadas {len(rows)} líneas internacionales")
            return rows
            
        except Exception as e:
            print(f"[ERROR] Error al obtener reporte internacional: {e}")
            import traceback
            traceback.print_exc()
            return []

