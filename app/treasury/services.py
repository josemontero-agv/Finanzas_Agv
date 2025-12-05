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
    
    def get_filter_options(self):
        """
        Obtiene opciones para filtros de tesorería.
        Retorna todos los tipos de documento disponibles (sin filtrar por tipo específico).
        
        Returns:
            dict: Diccionario con las opciones de filtros
        """
        try:
            if not self.repository.is_connected():
                return {'document_types': []}
            
            # Obtener tipos de documento LATAM
            document_types = []
            try:
                doc_types = self.repository.search_read(
                    'l10n_latam.document.type',
                    [],
                    ['id', 'name'],
                    limit=200
                )
                
                document_types = [
                    {'id': doc['id'], 'name': doc.get('name', '')}
                    for doc in doc_types
                ]
                document_types.sort(key=lambda x: x['name'])
            except Exception as e:
                print(f"[WARN] No se pudo obtener tipos de documento: {e}")
            
            return {
                'document_types': document_types
            }
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo opciones de filtros: {e}")
            return {'document_types': []}

    def get_report_lines_paginated(self, page=1, per_page=50, **kwargs):
        """
        Obtiene líneas de reporte con paginación eficiente en Odoo y datos bancarios.
        
        Args:
            page (int): Número de página (1-indexed)
            per_page (int): Registros por página
            **kwargs: Filtros (start_date, end_date, supplier, account_codes, doc_type_id, payment_state)
        
        Returns:
            dict: Datos paginados con metadatos
        """
        try:
            print(f"[INFO] Obteniendo página {page} de CxP (per_page={per_page})")
            
            if not self.repository.is_connected():
                raise ValueError("No hay conexión a Odoo disponible")
            
            # Extraer filtros
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            supplier = kwargs.get('supplier')
            account_codes = kwargs.get('account_codes')
            payment_state = kwargs.get('payment_state')
            doc_type_id = kwargs.get('doc_type_id')
            
            # Construir dominio
            # Códigos de cuenta para CxP
            if account_codes:
                codes = [c.strip() for c in account_codes.split(',') if c.strip()]
            else:
                codes = ['42', '421', '422', '423', '43', '431', '432','433']
            
            # Construir dominio base
            line_domain = [
                ('parent_state', '=', 'posted'),  # Solo facturas contabilizadas
                ('reconciled', '=', False),  # Solo pendientes de pago
                ('move_id.move_type', 'in', ['in_invoice', 'in_refund', 'entry']),
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
            if doc_type_id:
                line_domain.append(('move_id.l10n_latam_document_type_id', '=', doc_type_id))
            
            # 1. Obtener TOTAL de registros
            total_count = self.repository.search_count('account.move.line', line_domain)
            
            # 2. Calcular offset y validar página
            offset = (page - 1) * per_page
            if offset >= total_count and page > 1:
                return {
                    'data': [],
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page,
                    'has_more': False
                }
            
            # 3. Obtener SOLO los registros de esta página
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
                'reconciled', 'full_reconcile_id', 'blocked', 'debit', 'credit',
            ]
            
            lines = self.repository.search_read(
                'account.move.line',
                line_domain,
                line_fields,
                limit=per_page,
                offset=offset,
                order='date desc'
            )
            
            if not lines:
                return {
                    'data': [],
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page,
                    'has_more': False
                }
            
            # 4. Procesar líneas y obtener datos relacionados
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            account_ids = list(set([l['account_id'][0] for l in lines if l.get('account_id')]))
            
            move_map = self._get_moves_data(move_ids)
            partner_map = self._get_partners_data(partner_ids)
            account_map = self._get_accounts_data(account_ids)
            
            # --- LÓGICA DE BANCOS ---
            bank_map = {}
            if partner_ids:
                try:
                    # 1. Recolectar todos los bank_ids de los partners
                    all_bank_ids = []
                    partner_bank_ids_map = {} # partner_id -> [bank_ids]
                    
                    for pid in partner_ids:
                        partner = partner_map.get(pid)
                        if partner and partner.get('bank_ids'):
                            b_ids = partner['bank_ids']
                            partner_bank_ids_map[pid] = b_ids
                            all_bank_ids.extend(b_ids)
                    
                    # 2. Leer datos de los bancos
                    if all_bank_ids:
                        # Campos a leer de res.partner.bank
                        # bank_id (relacion), currency_id, acc_number, cci (si existe)
                        bank_fields = ['id', 'bank_id', 'currency_id', 'acc_number']
                        
                        # Intentar determinar si existe campo cci
                        # Por defecto asumimos que podría estar, Odoo no falla si pides un campo que no existe en read? 
                        # Odoo SÍ falla si el campo no existe en read. 
                        # Para estar seguros, primero inspeccionamos o asumimos estándar.
                        # Como el usuario pidió explícitamente 'cci', voy a intentar leerlo.
                        # Si falla, haré un fallback.
                        try:
                            # Intento optimista
                            banks_data = self.repository.read('res.partner.bank', all_bank_ids, bank_fields + ['cci'])
                        except Exception:
                            # Fallback sin cci
                            print("[WARN] Campo 'cci' no encontrado en res.partner.bank, intentando sin él")
                            banks_data = self.repository.read('res.partner.bank', all_bank_ids, bank_fields)
                        
                        # Crear mapa de bank_id -> data
                        banks_data_map = {b['id']: b for b in banks_data}
                        
                        # 3. Asociar bancos al partner
                        for pid, b_ids in partner_bank_ids_map.items():
                            # Tomamos el PRIMER banco para mostrar en la tabla (o concatenamos)
                            # Usuario pidió los campos, mostraremos el primero que tenga datos
                            first_bank = None
                            for bid in b_ids:
                                b_data = banks_data_map.get(bid)
                                if b_data:
                                    first_bank = b_data
                                    break
                            
                            if first_bank:
                                bank_name = self._extract_m2o_name(first_bank.get('bank_id'))
                                currency = self._extract_m2o_name(first_bank.get('currency_id'))
                                acc_number = first_bank.get('acc_number', '')
                                cci = first_bank.get('cci', '')
                                
                                bank_map[pid] = {
                                    'bank_name': bank_name,
                                    'bank_currency': currency,
                                    'bank_acc_number': acc_number,
                                    'bank_cci': cci
                                }

                except Exception as e:
                    print(f"[ERROR] Error obteniendo datos bancarios: {e}")

            # Combinar y procesar datos
            rows = self._process_payable_lines(lines, move_map, partner_map, account_map, bank_map)
            
            # 5. Metadatos
            total_pages = (total_count + per_page - 1) // per_page
            has_more = page < total_pages
            
            print(f"[OK] Procesados {len(rows)} registros paginados")
            
            return {
                'data': rows,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_more': has_more
            }
            
        except Exception as e:
            print(f"[ERROR] Error en paginación CxP: {e}")
            import traceback
            traceback.print_exc()
            raise

    def get_accounts_payable_report(self, start_date=None, end_date=None, 
                                    supplier=None, limit=0, account_codes=None,
                                    payment_state=None, doc_type_id=None):
        """
        DEPRECATED: Usar get_report_lines_paginated para mejor rendimiento.
        Mantenido por compatibilidad temporal.
        """
        # Redirigir a la versión paginada solicitando "todas" (o muchas) líneas si limit=0
        limit_val = limit if limit and limit > 0 else 10000
        result = self.get_report_lines_paginated(
            page=1, per_page=limit_val,
            start_date=start_date, end_date=end_date,
            supplier=supplier, account_codes=account_codes,
            payment_state=payment_state, doc_type_id=doc_type_id
        )
        return result['data']
    
    def _get_moves_data(self, move_ids):
        """
        Obtiene datos de las facturas (account.move).
        """
        if not move_ids:
            return {}
        
        move_fields = [
            'id', 'name', 'ref', 'payment_state', 'invoice_date', 
            'invoice_date_due', 'invoice_origin', 'amount_total',
            'amount_residual', 'amount_total_in_currency_signed', 'amount_residual_with_retention', 
            'amount_total_signed', 'currency_id', 'invoice_payment_term_id',
            'invoice_user_id', 'company_id', 'move_type',
            'l10n_latam_document_type_id', 'narration', 'state',
            'fiscal_position_id', 'invoice_incoterm_id'
        ]
        
        moves = self.repository.read('account.move', move_ids, move_fields)
        return {m['id']: m for m in moves}
    
    def _get_partners_data(self, partner_ids):
        """
        Obtiene datos de proveedores (res.partner).
        """
        if not partner_ids:
            return {}
        
        # Añadido bank_ids
        partner_fields = [
            'id', 'name', 'vat', 'country_id', 'country_code',
            'state_id', 'city', 'phone', 'email', 'supplier_rank', 'bank_ids'
        ]
        
        partners = self.repository.read('res.partner', partner_ids, partner_fields)
        return {p['id']: p for p in partners}
    
    def _get_accounts_data(self, account_ids):
        """
        Obtiene datos de cuentas contables (account.account).
        """
        if not account_ids:
            return {}
        
        accounts = self.repository.read('account.account', account_ids, ['id', 'code', 'name'])
        return {a['id']: a for a in accounts}
    
    def _process_payable_lines(self, lines, move_map, partner_map, account_map, bank_map=None):
        """
        Procesa las líneas de CxP y combina con datos relacionados.
        Añadido bank_map opcional.
        """
        rows = []
        today = datetime.today().date()
        if bank_map is None:
            bank_map = {}
        
        # Mapas de traducción
        PAYMENT_STATE_MAP = {
            'not_paid': 'No Pagado',
            'in_payment': 'En Proceso',
            'paid': 'Pagado',
            'partial': 'Parcial',
            'reversed': 'Revertido',
            'invoicing_legacy': 'Histórico'
        }
        
        STATE_MAP = {
            'draft': 'Borrador',
            'posted': 'Publicado',
            'cancel': 'Cancelado'
        }
        
        for line in lines:
            move_id = line['move_id'][0] if line.get('move_id') else None
            partner_id = line['partner_id'][0] if line.get('partner_id') else None
            account_id = line['account_id'][0] if line.get('account_id') else None
            
            move = move_map.get(move_id, {})
            partner = partner_map.get(partner_id, {})
            account = account_map.get(account_id, {})
            bank_info = bank_map.get(partner_id, {})
            
            # Calcular días de vencimiento
            invoice_date_due = move.get('invoice_date_due', '')
            date_due = line.get('date_maturity') or invoice_date_due
            dias_vencido = calcular_dias_vencido(date_due, today) if date_due else 0
            
            antiguedad = clasificar_antiguedad(max(0, dias_vencido))
            estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'
            
            debit = line.get('debit', 0.0) or 0.0
            credit = line.get('credit', 0.0) or 0.0
            amount_total_line = abs(debit - credit)
            amount_residual_line = abs(line.get('amount_residual', 0.0) or 0.0)
            
            payment_state_raw = move.get('payment_state', '')
            state_raw = move.get('state', '')
            
            row = {
                # Datos de la factura
                'move_name': move.get('name', ''),
                'ref': move.get('ref', ''),
                'payment_state': PAYMENT_STATE_MAP.get(payment_state_raw, payment_state_raw),
                'move_type': move.get('move_type', ''),
                'state': STATE_MAP.get(state_raw, state_raw),
                'invoice_date': move.get('invoice_date', ''),
                'invoice_date_due': invoice_date_due,
                'invoice_origin': move.get('invoice_origin', ''),
                'invoice_payment_term_id': self._extract_m2o_name(move.get('invoice_payment_term_id')),
                # 'invoice_user_id': self._extract_m2o_name(move.get('invoice_user_id')), # REMOVED per user request (aunque sigo extrayendo, no lo mostraré en front, pero si no cuesta dejarlo...)
                # El usuario pidió sacarlo del REPORTE (HTML), no necesariamente del backend. Lo dejo por si acaso lo piden luego.
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
                
                # Datos Bancarios (Nuevos)
                'bank_name': bank_info.get('bank_name', ''),
                'bank_currency': bank_info.get('bank_currency', ''),
                'bank_acc_number': bank_info.get('bank_acc_number', ''),
                'bank_cci': bank_info.get('bank_cci', ''),
                
                # Datos de la cuenta contable
                'account_code': account.get('code', ''),
                'account_name': account.get('name', ''),
                
                # Montos
                'currency_id': self._extract_m2o_name(line.get('currency_id') or move.get('currency_id')),
                'amount_total': amount_total_line,
                'amount_residual': amount_residual_line,
                'amount_total_in_currency_signed': move.get('amount_total_in_currency_signed', 0.0),
                'amount_residual_with_retention': move.get('amount_residual_with_retention', 0.0),
                'amount_total_signed': move.get('amount_total_signed', 0.0),
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
        """
        if isinstance(value, list) and len(value) >= 2:
            return value[1]
        return ''

