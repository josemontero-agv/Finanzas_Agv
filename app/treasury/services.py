# -*- coding: utf-8 -*-
"""
Servicio de Tesorería (Treasury).

Lógica de negocio para reportes de cuentas por pagar (CxP).
Implementa reportes para cuentas contables 42 y 43.
"""

from datetime import datetime
from app.core.calculators import calcular_dias_vencido, clasificar_antiguedad


class TreasuryService:
    """
    Servicio para generar reportes de cuentas por pagar (Tesorería).
    
    Responsabilidades:
    - Obtener líneas de CxP de las cuentas 42 y 43
    - Calcular días de vencimiento
    - Clasificar antigüedad de deudas por pagar
    - Filtrar por proveedor, fecha, estado de pago
    """
    
    def __init__(self, odoo_repository):
        """
        Inicializa el servicio de tesorería.
        
        Args:
            odoo_repository (OdooRepository): Instancia del repositorio de Odoo
        """
        self.repository = odoo_repository
    
    def get_accounts_payable_report(self, start_date=None, end_date=None, 
                                    supplier=None, limit=0, account_codes=None,
                                    payment_state=None):
        """
        Obtener reporte de cuentas por pagar (Cuenta 42 y 43).
        
        Cuentas relevantes:
        - 42: Cuentas por pagar comerciales - Terceros
        - 43: Cuentas por pagar comerciales - Relacionadas
        
        Args:
            start_date (str): Fecha inicial (formato: YYYY-MM-DD)
            end_date (str): Fecha final (formato: YYYY-MM-DD)
            supplier (str): Nombre del proveedor a filtrar
            limit (int): Límite de registros (0 = sin límite)
            account_codes (str): Códigos de cuenta separados por coma
            payment_state (str): Estado de pago ('not_paid', 'in_payment', 'paid', 'partial')
        
        Returns:
            list: Líneas de reporte CxP con información de proveedores y cálculos
        """
        try:
            print("[INFO] Obteniendo reporte de cuentas por pagar...")
            
            if not self.repository.is_connected():
                print("[ERROR] No hay conexión a Odoo disponible")
                return []
            
            # Códigos de cuenta para CxP
            if account_codes:
                codes = [c.strip() for c in account_codes.split(',') if c.strip()]
            else:
                codes = ['42', '421', '422', '423', '43', '431', '432']  # Cuentas CxP por defecto
            
            # Construir dominio base
            line_domain = [
                ('parent_state', '=', 'posted'),  # Solo facturas contabilizadas
                ('reconciled', '=', False),  # Solo pendientes de pago
                ('move_id.move_type', 'in', ['in_invoice', 'in_refund']),  # Facturas de proveedor
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
            
            # Filtros adicionales
            if start_date:
                line_domain.append(('date', '>=', start_date))
            if end_date:
                line_domain.append(('date', '<=', end_date))
            if supplier:
                line_domain.append(('partner_id.name', 'ilike', supplier))
            if payment_state:
                line_domain.append(('move_id.payment_state', '=', payment_state))
            
            # Campos a extraer de account.move.line (expandido)
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
                'reconciled', 'full_reconcile_id', 'blocked',
            ]
            
            effective_limit = limit if limit and limit > 0 else 10000
            lines = self.repository.search_read(
                'account.move.line', line_domain, line_fields,
                limit=effective_limit
            )
            
            print(f"[OK] Obtenidas {len(lines)} líneas de cuentas por pagar")
            
            if not lines:
                return []
            
            # Extraer IDs únicos para consultas relacionadas
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            account_ids = list(set([l['account_id'][0] for l in lines if l.get('account_id')]))
            
            # Obtener datos de facturas (account.move)
            move_map = self._get_moves_data(move_ids)
            
            # Obtener datos de proveedores (res.partner)
            partner_map = self._get_partners_data(partner_ids)
            
            # Obtener datos de cuentas contables (account.account)
            account_map = self._get_accounts_data(account_ids)
            
            # Combinar y procesar datos
            rows = self._process_payable_lines(lines, move_map, partner_map, account_map)
            
            print(f"[OK] Procesadas {len(rows)} líneas de CxP")
            return rows
            
        except Exception as e:
            print(f"[ERROR] Error al obtener reporte de cuentas por pagar: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _get_moves_data(self, move_ids):
        """
        Obtiene datos de las facturas (account.move).
        
        Args:
            move_ids (list): Lista de IDs de account.move
        
        Returns:
            dict: Mapeo de move_id -> datos de factura
        """
        if not move_ids:
            return {}
        
        move_fields = [
            'id', 'name', 'ref', 'payment_state', 'invoice_date', 
            'invoice_date_due', 'invoice_origin', 'amount_total',
            'amount_residual', 'currency_id', 'invoice_payment_term_id',
            'invoice_user_id', 'company_id', 'move_type',
            'l10n_latam_document_type_id', 'narration', 'state',
            'fiscal_position_id', 'invoice_incoterm_id'
        ]
        
        moves = self.repository.read('account.move', move_ids, move_fields)
        return {m['id']: m for m in moves}
    
    def _get_partners_data(self, partner_ids):
        """
        Obtiene datos de proveedores (res.partner).
        
        Args:
            partner_ids (list): Lista de IDs de res.partner
        
        Returns:
            dict: Mapeo de partner_id -> datos de proveedor
        """
        if not partner_ids:
            return {}
        
        partner_fields = [
            'id', 'name', 'vat', 'country_id', 'country_code',
            'state_id', 'city', 'phone', 'email', 'supplier_rank'
        ]
        
        partners = self.repository.read('res.partner', partner_ids, partner_fields)
        return {p['id']: p for p in partners}
    
    def _get_accounts_data(self, account_ids):
        """
        Obtiene datos de cuentas contables (account.account).
        
        Args:
            account_ids (list): Lista de IDs de account.account
        
        Returns:
            dict: Mapeo de account_id -> datos de cuenta
        """
        if not account_ids:
            return {}
        
        accounts = self.repository.read('account.account', account_ids, ['id', 'code', 'name'])
        return {a['id']: a for a in accounts}
    
    def _process_payable_lines(self, lines, move_map, partner_map, account_map):
        """
        Procesa las líneas de CxP y combina con datos relacionados.
        
        Args:
            lines (list): Líneas de account.move.line
            move_map (dict): Datos de facturas
            partner_map (dict): Datos de proveedores
            account_map (dict): Datos de cuentas
        
        Returns:
            list: Líneas procesadas con todos los datos combinados
        """
        rows = []
        today = datetime.today().date()
        
        for line in lines:
            move_id = line['move_id'][0] if line.get('move_id') else None
            partner_id = line['partner_id'][0] if line.get('partner_id') else None
            account_id = line['account_id'][0] if line.get('account_id') else None
            
            move = move_map.get(move_id, {})
            partner = partner_map.get(partner_id, {})
            account = account_map.get(account_id, {})
            
            # Calcular días de vencimiento
            invoice_date_due = move.get('invoice_date_due', '')
            dias_vencido = calcular_dias_vencido(invoice_date_due, today) if invoice_date_due else 0
            
            # Clasificar antigüedad
            antiguedad = clasificar_antiguedad(max(0, dias_vencido))
            
            # Estado de deuda
            estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'
            
            row = {
                # Datos de la factura
                'move_name': move.get('name', ''),
                'ref': move.get('ref', ''),
                'payment_state': move.get('payment_state', ''),
                'move_type': move.get('move_type', ''),
                'state': move.get('state', ''),
                'invoice_date': move.get('invoice_date', ''),
                'invoice_date_due': invoice_date_due,
                'invoice_origin': move.get('invoice_origin', ''),
                'invoice_payment_term_id': self._extract_m2o_name(move.get('invoice_payment_term_id')),
                'invoice_user_id': self._extract_m2o_name(move.get('invoice_user_id')),
                'l10n_latam_document_type_id': self._extract_m2o_name(move.get('l10n_latam_document_type_id')),
                'narration': move.get('narration', ''),
                'fiscal_position_id': self._extract_m2o_name(move.get('fiscal_position_id')),
                'invoice_incoterm_id': self._extract_m2o_name(move.get('invoice_incoterm_id')),
                'company_id': self._extract_m2o_name(move.get('company_id')),
                
                # Datos del proveedor
                'supplier_vat': partner.get('vat', ''),
                'supplier_name': partner.get('name', ''),
                'supplier_country': self._extract_m2o_name(partner.get('country_id')),
                'supplier_country_code': partner.get('country_code', ''),
                'supplier_state': self._extract_m2o_name(partner.get('state_id')),
                'supplier_city': partner.get('city', ''),
                'supplier_phone': partner.get('phone', ''),
                'supplier_email': partner.get('email', ''),
                'supplier_rank': partner.get('supplier_rank', 0),
                
                # Datos de la cuenta contable
                'account_code': account.get('code', ''),
                'account_name': account.get('name', ''),
                
                # Montos
                'currency_id': self._extract_m2o_name(line.get('currency_id') or move.get('currency_id')),
                'amount_total': move.get('amount_total', 0.0),
                'amount_residual': move.get('amount_residual', 0.0),
                'amount_currency': line.get('amount_currency', 0.0),
                'amount_residual_currency': line.get('amount_residual', 0.0),
                
                # Fechas y línea
                'date': line.get('date', ''),
                'date_maturity': line.get('date_maturity', ''),
                'name': line.get('name', ''),
                'reconciled': line.get('reconciled', False),
                'blocked': line.get('blocked', False),
                'full_reconcile_id': self._extract_m2o_name(line.get('full_reconcile_id')),
                
                # Campos calculados
                'dias_vencido': dias_vencido,
                'estado_deuda': estado_deuda,
                'antiguedad': antiguedad,
            }
            
            rows.append(row)
        
        return rows
    
    @staticmethod
    def _extract_m2o_name(value):
        """
        Extrae el nombre de un campo Many2One de Odoo.
        
        Args:
            value: Valor del campo M2O (puede ser lista [id, name] o False)
        
        Returns:
            str: Nombre extraído o cadena vacía
        """
        if isinstance(value, list) and len(value) >= 2:
            return value[1]
        return ''
    
    def get_summary_by_supplier(self, start_date=None, end_date=None):
        """
        Obtiene resumen de CxP agrupado por proveedor.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
        
        Returns:
            list: Resumen con totales por proveedor
        """
        lines = self.get_accounts_payable_report(start_date, end_date)
        
        # Agrupar por proveedor
        suppliers_summary = {}
        
        for line in lines:
            supplier = line['supplier_name']
            if supplier not in suppliers_summary:
                suppliers_summary[supplier] = {
                    'supplier_name': supplier,
                    'supplier_vat': line['supplier_vat'],
                    'total_debt': 0.0,
                    'total_overdue': 0.0,
                    'count_invoices': 0,
                    'oldest_invoice_days': 0
                }
            
            suppliers_summary[supplier]['total_debt'] += line['amount_residual']
            suppliers_summary[supplier]['count_invoices'] += 1
            
            if line['dias_vencido'] > 0:
                suppliers_summary[supplier]['total_overdue'] += line['amount_residual']
            
            if line['dias_vencido'] > suppliers_summary[supplier]['oldest_invoice_days']:
                suppliers_summary[supplier]['oldest_invoice_days'] = line['dias_vencido']
        
        return list(suppliers_summary.values())
    
    def get_summary_by_aging(self, start_date=None, end_date=None):
        """
        Obtiene resumen de CxP agrupado por antigüedad.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
        
        Returns:
            dict: Resumen con totales por rango de antigüedad
        """
        lines = self.get_accounts_payable_report(start_date, end_date)
        
        aging_summary = {
            'Vigente': {'count': 0, 'amount': 0.0},
            'Atraso Corto (1-30)': {'count': 0, 'amount': 0.0},
            'Atraso Medio (31-60)': {'count': 0, 'amount': 0.0},
            'Atraso Prolongado (61-90)': {'count': 0, 'amount': 0.0},
            'Cobranza Judicial (+90)': {'count': 0, 'amount': 0.0}
        }
        
        for line in lines:
            antiguedad = line['antiguedad']
            aging_summary[antiguedad]['count'] += 1
            aging_summary[antiguedad]['amount'] += line['amount_residual']
        
        return aging_summary
