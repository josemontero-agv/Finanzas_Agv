# -*- coding: utf-8 -*-
"""
Servicio de Tesorería (Treasury).

Lógica de negocio para reportes de cuentas por pagar (CxP).
Implementa reportes para cuentas contables 42 y 43.
"""

from datetime import datetime
from app.core.calculators import calcular_dias_vencido, clasificar_antiguedad
from app.core.supabase import SupabaseClient


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
        Obtiene líneas de reporte con paginación eficiente en Odoo.
        Soporta 'Fecha de Corte' (Historical Reporting).
        
        Args:
            page (int): Número de página (1-indexed)
            per_page (int): Registros por página
            **kwargs: Filtros (start_date, end_date, supplier, account_codes, doc_type_id, payment_state, cutoff_date)
        
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
            cutoff_date = kwargs.get('cutoff_date') # NUEVO: Fecha de corte
            supplier = kwargs.get('supplier')
            account_codes = kwargs.get('account_codes')
            payment_state = kwargs.get('payment_state')
            doc_type_id = kwargs.get('doc_type_id')
            reference = kwargs.get('reference')
            has_retention = kwargs.get('has_retention') # NUEVO: Filtro retención
            has_origin = kwargs.get('has_origin') # NUEVO: Filtro origen
            only_vouchers = kwargs.get('only_vouchers', False) # NUEVO: Solo comprobantes
            include_reconciled = kwargs.get('include_reconciled', False) # NUEVO: Incluir conciliados
            
            # Construir dominio
            # Códigos de cuenta para CxP
            if account_codes:
                codes = [c.strip() for c in account_codes.split(',') if c.strip()]
            else:
                codes = ['42', '421', '422', '423', '43', '431', '432','433']
            
            # Construir dominio base
            # Definir tipos de movimientos según filtro "Solo Comprobantes"
            if only_vouchers:
                # Solo comprobantes: facturas, notas de crédito, recibos, pagos
                move_types = ['in_invoice', 'in_refund', 'in_receipt', 'in_payment']
            else:
                # Todos los movimientos: incluir también asientos manuales (entry)
                move_types = ['in_invoice', 'in_refund', 'entry', 'in_receipt', 'in_payment']

            line_domain = [
                ('parent_state', '=', 'posted'),  # Solo facturas contabilizadas
                ('move_id.move_type', 'in', move_types),
            ]
            
            # Lógica de Fecha de Corte (Historical) vs Reporte Actual
            if cutoff_date:
                # Modo Histórico: Traer TODO lo que existía antes del corte
                line_domain.append(('date', '<=', cutoff_date))
                # NO filtramos por reconciled=False, porque algo pagado hoy pudo estar abierto antes
            else:
                # Modo Actual (Default)
                if not include_reconciled:
                    line_domain.append(('reconciled', '=', False))
                
                if start_date:
                    line_domain.append(('date', '>=', start_date))
                if end_date:
                    line_domain.append(('date', '<=', end_date))
            
            # Construir OR para códigos de cuenta
            if len(codes) > 1:
                or_operators = ['|'] * (len(codes) - 1)
                code_conditions = []
                for code in codes:
                    # Si el usuario pasa un código "completo" (ej: 4230002), hacemos match exacto.
                    # Si pasa un prefijo (ej: 42, 423), usamos prefijo.
                    is_exact = code.isdigit() and len(code) >= 6
                    if is_exact:
                        code_conditions.append(('account_id.code', '=', code))
                    else:
                        code_conditions.append(('account_id.code', '=like', f'{code}%'))
                line_domain = or_operators + code_conditions + line_domain
            else:
                code0 = codes[0]
                is_exact = code0.isdigit() and len(code0) >= 6
                if is_exact:
                    line_domain.insert(0, ('account_id.code', '=', code0))
                else:
                    line_domain.insert(0, ('account_id.code', '=like', f'{code0}%'))
            
            # Filtros adicionales
            if not cutoff_date: # Solo aplicar filtro de fecha normal si no es reporte historico
                if start_date:
                    line_domain.append(('date', '>=', start_date))
                if end_date:
                    line_domain.append(('date', '<=', end_date))
            
            if supplier:
                line_domain.append(('partner_id.name', 'ilike', supplier))
            if payment_state and not cutoff_date: # Estado de pago actual solo sirve en reporte actual
                line_domain.append(('move_id.payment_state', '=', payment_state))
            if doc_type_id:
                line_domain.append(('move_id.l10n_latam_document_type_id', '=', doc_type_id))
            if reference:
                line_domain.append(('move_id.ref', 'ilike', reference.strip()))
            if has_retention:
                line_domain.append(('move_id.l10n_pe_retention_check', '=', True))
            if has_origin:
                line_domain.append(('move_id.invoice_origin', '!=', False))
            
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
                'matched_debit_ids', 'matched_credit_ids' # Necesarios para calcular fecha de pago real
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
            
            # Obtener datos de conciliaciones para reporte histórico (fechas y montos)
            reconciliation_map = {}
            if cutoff_date:
                reconciliation_map = self._get_reconciliation_amounts(lines, cutoff_date)
            
            move_map = self._get_moves_data(move_ids)
            partner_map = self._get_partners_data(partner_ids)
            account_map = self._get_accounts_data(account_ids)

            # Combinar y procesar datos
            rows = self._process_payable_lines(
                lines,
                move_map,
                partner_map,
                account_map,
                cutoff_date,
                reconciliation_map,
                include_reconciled
            )
            
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

    def get_accounts_payable_report(self, start_date=None, end_date=None, cutoff_date=None,
                                    supplier=None, limit=0, account_codes=None,
                                    payment_state=None, doc_type_id=None, reference=None,
                                    has_retention=None, has_origin=None, only_vouchers=False,
                                    include_reconciled=False):
        """
        DEPRECATED: Usar get_report_lines_paginated para mejor rendimiento.
        Mantenido por compatibilidad temporal.

        Args:
            start_date: Fecha inicial
            end_date: Fecha final
            cutoff_date: Fecha de corte para reporte histórico
            supplier: Filtro por proveedor
            limit: Límite de registros
            account_codes: Códigos de cuenta
            payment_state: Estado de pago
            doc_type_id: Tipo de documento
            reference: Referencia
            has_retention: Solo con retención
            has_origin: Solo con origen
            only_vouchers: Solo comprobantes (excluir asientos manuales)
            include_reconciled: Incluir conciliados
        """
        # Redirigir a la versión paginada solicitando "todas" (o muchas) líneas si limit=0
        limit_val = limit if limit and limit > 0 else 10000
        result = self.get_report_lines_paginated(
            page=1, per_page=limit_val,
            start_date=start_date, end_date=end_date,
            cutoff_date=cutoff_date,
            supplier=supplier, account_codes=account_codes,
            payment_state=payment_state, doc_type_id=doc_type_id,
            reference=reference,
            has_retention=has_retention, has_origin=has_origin,
            only_vouchers=only_vouchers,
            include_reconciled=include_reconciled
        )
        return result['data']
    
    def get_supplier_bank_accounts(self, supplier_name=None):
        """
        Obtiene reporte de cuentas bancarias de proveedores.
        
        Args:
            supplier_name (str, optional): Filtro por nombre de proveedor
            
        Returns:
            list: Lista de cuentas bancarias de proveedores
        """
        try:
            if not self.repository.is_connected():
                raise ValueError("No hay conexión a Odoo disponible")

            # 1. Buscar proveedores
            domain = [('supplier_rank', '>', 0)]
            if supplier_name:
                domain.append(('name', 'ilike', supplier_name))

            # Obtener IDs de partners
            # Leemos directamente los campos necesarios incluyendo bank_ids
            partners = self.repository.search_read(
                'res.partner',
                domain,
                ['id', 'name', 'vat', 'bank_ids', 'country_id', 'email', 'phone'],
                limit=2000  # Limite razonable
            )
            
            if not partners:
                return []

            # 2. Recolectar IDs de bancos
            all_bank_ids = []
            partner_map = {}
            
            for p in partners:
                partner_map[p['id']] = p
                if p.get('bank_ids'):
                    all_bank_ids.extend(p['bank_ids'])
            
            if not all_bank_ids:
                return []
            
            # 3. Leer detalles de bancos (res.partner.bank)
            bank_fields = ['id', 'bank_id', 'currency_id', 'acc_number', 'partner_id']
            
            try:
                banks_data = self.repository.read('res.partner.bank', all_bank_ids, bank_fields + ['cci'])
            except Exception:
                # Fallback sin cci si no existe el campo
                print("[WARN] Campo 'cci' no encontrado en res.partner.bank")
                banks_data = self.repository.read('res.partner.bank', all_bank_ids, bank_fields)
                
            # 4. Construir reporte plano
            report_rows = []
            
            for bank_record in banks_data:
                # Obtener partner asociado al banco
                # El campo partner_id en res.partner.bank es Many2One al partner dueño
                partner_id_raw = bank_record.get('partner_id')
                if not partner_id_raw:
                    continue
                    
                partner_id = partner_id_raw[0]
                partner = partner_map.get(partner_id)
                
                if not partner:
                    # Si no lo encontramos en nuestro mapa inicial (por filtros), lo saltamos
                    # O podríamos hacer fetch si es crítico, pero asumimos consistencia por bank_ids
                    continue
                
                row = {
                    'supplier_name': partner.get('name', ''),
                    'supplier_vat': partner.get('vat', ''),
                    'supplier_email': partner.get('email', ''),
                    'supplier_country': self._extract_m2o_name(partner.get('country_id')),
                    
                    'bank_name': self._extract_m2o_name(bank_record.get('bank_id')),
                    'currency': self._extract_m2o_name(bank_record.get('currency_id')),
                    'acc_number': bank_record.get('acc_number', ''),
                    'cci': bank_record.get('cci', ''),
                }
                report_rows.append(row)
                
            # Ordenar por nombre de proveedor
            report_rows.sort(key=lambda x: x['supplier_name'])
            
            return report_rows
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo cuentas bancarias: {e}")
            import traceback
            traceback.print_exc()
            raise
    
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
            'fiscal_position_id', 'invoice_incoterm_id', 'l10n_pe_retention_check',
            'l10n_latam_boe_number'  # Número de letra de cambio
        ]
        
        moves = self.repository.read('account.move', move_ids, move_fields)
        return {m['id']: m for m in moves}
    
    def _get_partners_data(self, partner_ids):
        """
        Obtiene datos de proveedores (res.partner).
        """
        if not partner_ids:
            return {}
        
        # bank_ids ya no es necesario aquí para el reporte principal, pero no hace daño dejarlo
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
    
    def _get_reconciliation_amounts(self, lines, cutoff_date=None):
        """
        Obtiene montos conciliados por línea y separa pagos antes/después del corte.
        Retorna dict: {
            line_id: {
                'max_date': 'YYYY-MM-DD' | None,
                'paid_before': float,
                'paid_after': float
            }
        }
        """
        reconcile_ids = set()
        line_to_reconcile_map = {}  # line_id -> [partial_ids]
        
        for line in lines:
            partials = (line.get('matched_debit_ids') or []) + (line.get('matched_credit_ids') or [])
            if partials:
                reconcile_ids.update(partials)
                line_to_reconcile_map[line['id']] = partials
        
        if not reconcile_ids:
            return {}
        
        fields = ['max_date', 'amount']
        partials_data = self.repository.read('account.partial.reconcile', list(reconcile_ids), fields)
        partial_date_map = {p['id']: p for p in partials_data}
        
        line_map = {}
        for line_id, partials in line_to_reconcile_map.items():
            max_date = None
            paid_before = 0.0
            paid_after = 0.0
            for pid in partials:
                pdata = partial_date_map.get(pid)
                if not pdata:
                    continue
                pdate = pdata.get('max_date')
                amount = float(pdata.get('amount', 0.0) or 0.0)
                if pdate:
                    if not max_date or pdate > max_date:
                        max_date = pdate
                    if cutoff_date:
                        if pdate > cutoff_date:
                            paid_after += amount
                        else:
                            paid_before += amount
                else:
                    # Sin fecha, considerar como antes del corte por seguridad
                    paid_before += amount
            line_map[line_id] = {
                'max_date': max_date,
                'paid_before': paid_before,
                'paid_after': paid_after
            }
        
        return line_map

    def _process_payable_lines(self, lines, move_map, partner_map, account_map, cutoff_date=None, reconciliation_map=None, include_reconciled=False):
        """
        Procesa las líneas de CxP y combina con datos relacionados.
        Si cutoff_date está presente, recalcula estado histórico.
        """
        rows = []
        # Si es histórico, el día de referencia es el corte. Si no, es hoy.
        today = datetime.strptime(cutoff_date, '%Y-%m-%d').date() if cutoff_date else datetime.today().date()
        
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
            rec_info = reconciliation_map.get(line['id'], {}) if reconciliation_map else {}
            reconcile_date = rec_info.get('max_date')
            paid_after_cutoff = float(rec_info.get('paid_after', 0.0) or 0.0)
            paid_before_cutoff = float(rec_info.get('paid_before', 0.0) or 0.0)

            # Lógica de Filtrado Histórico (Post-Fetch)
            if cutoff_date:
                is_reconciled_now = line.get('reconciled', False)
                
                if is_reconciled_now and reconcile_date:
                    # Si se pagó antes o en el corte y no pedimos conciliados, omitir
                    if reconcile_date <= cutoff_date and not include_reconciled:
                        continue
                elif is_reconciled_now and not reconcile_date:
                    # Conciliado pero sin fecha: si no incluimos conciliados, omitir
                    if not include_reconciled:
                        continue

            move_id = line['move_id'][0] if line.get('move_id') else None
            partner_id = line['partner_id'][0] if line.get('partner_id') else None
            account_id = line['account_id'][0] if line.get('account_id') else None
            
            move = move_map.get(move_id, {})
            partner = partner_map.get(partner_id, {})
            account = account_map.get(account_id, {})
            
            # Calcular días de vencimiento
            invoice_date_due = move.get('invoice_date_due', '')
            date_due = line.get('date_maturity') or invoice_date_due
            dias_vencido = calcular_dias_vencido(date_due, today) if date_due else 0
            
            antiguedad = clasificar_antiguedad(max(0, dias_vencido))
            estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'
            
            debit = line.get('debit', 0.0) or 0.0
            credit = line.get('credit', 0.0) or 0.0
            amount_total_line = abs(debit - credit)
            current_residual = abs(line.get('amount_residual', 0.0) or 0.0)
            amount_residual_line = current_residual
            amount_residual_historical = amount_residual_line

            paid_after_cutoff = paid_after_cutoff if cutoff_date else 0.0

            # Ajuste de montos para histórico con pagos después del corte
            if cutoff_date:
                # El pendiente histórico es el residual actual + lo pagado después del corte
                amount_residual_historical = current_residual + paid_after_cutoff
                if reconcile_date and reconcile_date <= cutoff_date and include_reconciled:
                    amount_residual_historical = 0.0
            
            payment_state_raw = move.get('payment_state', '')
            # Ajuste estado de pago visual
            payment_state_display = PAYMENT_STATE_MAP.get(payment_state_raw, payment_state_raw)
            if cutoff_date and amount_residual_historical > 0:
                payment_state_display = "No Pagado (al corte)"

            state_raw = move.get('state', '')
            
            row = {
                # Datos de la factura
                'move_name': move.get('name', ''),
                'ref': move.get('ref', ''),
                'payment_state': payment_state_display,
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
                'l10n_latam_boe_number': move.get('l10n_latam_boe_number', ''),  # Número de letra de cambio
                'narration': move.get('narration', ''),
                'fiscal_position_id': self._extract_m2o_name(move.get('fiscal_position_id')),
                'invoice_incoterm_id': self._extract_m2o_name(move.get('invoice_incoterm_id')),
                'company_id': self._extract_m2o_name(move.get('company_id')),
                
                # Datos del proveedor
                'supplier_vat': partner.get('vat', ''),
                'supplier_name': partner.get('name', ''),
                'supplier_country': self._extract_m2o_name(partner.get('country_id')),
                'supplier_state': self._extract_m2o_name(partner.get('state_id')),
                'supplier_city': partner.get('city', ''),
                'supplier_email': partner.get('email', ''),
                'supplier_rank': partner.get('supplier_rank', 0),
                
                # Datos de la cuenta contable
                'account_code': account.get('code', ''),
                'account_name': account.get('name', ''),
                
                # Montos
                'currency_id': self._extract_m2o_name(line.get('currency_id') or move.get('currency_id')),
                'amount_total': amount_total_line,
                'amount_residual': amount_residual_line,
                'amount_residual_historical': amount_residual_historical,
                'amount_total_in_currency_signed': move.get('amount_total_in_currency_signed', 0.0),
                'amount_residual_with_retention': move.get('amount_residual_with_retention', 0.0),
                'amount_total_signed': move.get('amount_total_signed', 0.0),
                'amount_currency': line.get('amount_currency', 0.0),
                'amount_residual_currency': line.get('amount_residual', 0.0),
                'paid_after_cutoff': paid_after_cutoff,
                'debit': debit,
                'credit': credit,
                
                # Fechas y línea
                'date': line.get('date', ''),
                'date_maturity': line.get('date_maturity', ''),
                'name': line.get('name', ''),
                'reconciled': line.get('reconciled', False),
                'blocked': line.get('blocked', False),
                'full_reconcile_id': self._extract_m2o_name(line.get('full_reconcile_id')),
                'reconciliation_date': reconcile_date if cutoff_date else '',
                
                # Campos calculados
                'dias_vencido': dias_vencido,
                'estado_deuda': estado_deuda,
                'antiguedad': antiguedad,
                'l10n_pe_retention_check': move.get('l10n_pe_retention_check', False),
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

    def get_netted_report_from_supabase(self, supplier=None):
        """
        Consulta la vista de reporte neteado en Supabase.
        
        Args:
            supplier (str, optional): Filtro por nombre de proveedor
            
        Returns:
            list: Datos del reporte neteado
        """
        try:
            supabase = SupabaseClient.get_client()
            if not supabase:
                print("[ERROR] No se pudo obtener el cliente de Supabase")
                return []

            # Consultar la vista que creamos en el dashboard
            # Usamos select("*") para traer todas las columnas definidas en view_treasury_netted_report
            query = supabase.table('view_treasury_netted_report').select("*")
            
            if supplier:
                query = query.ilike('supplier_name', f'%{supplier}%')
                
            # Ordenar por fecha de emisión descendente
            query = query.order('date_emitted', desc=True)
            
            response = query.execute()
            
            # Formatear los datos para que coincidan con lo que el frontend espera
            # (opcional, pero útil para mantener compatibilidad)
            formatted_data = []
            for row in response.data:
                # Re-clasificar antigüedad y días vencido si es necesario (o usar los de la vista)
                # Por ahora devolvemos tal cual viene de la vista
                formatted_data.append(row)
                
            return formatted_data
            
        except Exception as e:
            print(f"[ERROR] Error al consultar reporte neteado en Supabase: {e}")
            import traceback
            traceback.print_exc()
            return []
