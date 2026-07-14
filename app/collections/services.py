# -*- coding: utf-8 -*-
"""
Servicio de Cobranzas (Collections).

Lógica de negocio para reportes de cuentas por cobrar.
Migrado desde dashboard-Cobranzas/services/report_service.py
"""

from datetime import datetime
from app.core.calculators import calcular_mora, calcular_dias_vencido, clasificar_antiguedad

# Etiquetas en español para account.move.state (Estado Documento)
DOCUMENT_STATE_LABELS_ES = {
    'draft': 'Borrador',
    'posted': 'Publicado',
    'cancel': 'Cancelado',
    'to_accept': 'Por aceptar',
    'to_reconcile': 'Para Conciliar',
    'to_disburse': 'Por Desembolsar',
    'portfolio': 'Cartera',
    'accepted': 'Aceptada',
    'collection': 'Cobranza',
    'discount': 'Descuento',
    'warranty': 'Garantía',
    'disbursed': 'Desembolsado',
    'pending': 'Pendiente renovación',
    'protested': 'Protestado',
}

PAYMENT_STATE_LABELS_ES = {
    'not_paid': 'Sin Pagar',
    'in_payment': 'En Proceso',
    'paid': 'Pagado',
    'partial': 'Pago Parcial',
    'reversed': 'Revertido',
    'invoicing_legacy': 'Legado',
}


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

    @staticmethod
    def _chunked(items, size=500):
        """Divide una lista en lotes para evitar timeouts en XML-RPC."""
        if not items:
            return
        for idx in range(0, len(items), size):
            yield items[idx:idx + size]

    def _read_in_batches(self, model, ids, fields, batch_size=500):
        """Lee registros en lotes y retorna lista consolidada."""
        if not ids:
            return []
        results = []
        for batch in self._chunked(ids, batch_size):
            batch_records = self.repository.read(model, batch, fields) or []
            results.extend(batch_records)
        return results

    def _search_read_in_batches(self, model, in_field, ids, fields, batch_size=300):
        """Ejecuta search_read en lotes para dominios tipo ('field', 'in', ids)."""
        if not ids:
            return []
        results = []
        for batch in self._chunked(ids, batch_size):
            batch_records = self.repository.search_read(
                model,
                [(in_field, 'in', batch)],
                fields
            ) or []
            results.extend(batch_records)
        return results

    @staticmethod
    def _m2o_id(value):
        """Obtiene el ID de un many2one."""
        if isinstance(value, list) and len(value) >= 1:
            return value[0]
        return None

    @staticmethod
    def _has_value(value):
        return value not in (None, False, '', [])

    def _build_trace_invoice_map(self, move_map):
        """
        Construye mapeo move_id -> factura origen usando:
        1) bill_form_id -> invoice_ids (traza fuerte)
        2) fallback por l10n_latam_boe_number (traza por numero de letra)
        """
        trace_invoice_map = {}
        if not move_map:
            return trace_invoice_map

        # ---------- 1) Traza fuerte por bill_form_id ----------
        bill_form_ids = {
            self._m2o_id(m.get('bill_form_id'))
            for m in move_map.values()
            if self._m2o_id(m.get('bill_form_id'))
        }
        bill_form_map = {}
        source_invoice_map = {}
        if bill_form_ids:
            try:
                bill_forms = self._read_in_batches(
                    'account.bill.form',
                    list(bill_form_ids),
                    ['id', 'invoice_ids'],
                    batch_size=300
                )
                bill_form_map = {bf['id']: bf for bf in bill_forms}
                source_invoice_ids = set()
                for bf in bill_forms:
                    source_invoice_ids.update(bf.get('invoice_ids') or [])

                if source_invoice_ids:
                    source_invoices = self._read_in_batches(
                        'account.move',
                        list(source_invoice_ids),
                        [
                            'id', 'name', 'state', 'move_type', 'partner_id', 'amount_total',
                            'invoice_origin', 'invoice_payment_term_id', 'invoice_user_id',
                            'sales_channel_id', 'sale_type_id', 'team_id',
                            'bill_form_invoices_order_sales_line_commercial_zone_id'
                        ],
                        batch_size=300
                    )
                    source_invoice_map = {inv['id']: inv for inv in source_invoices}

                for move_id_key, move_data in move_map.items():
                    bf_id = self._m2o_id(move_data.get('bill_form_id'))
                    if not bf_id:
                        continue
                    bf = bill_form_map.get(bf_id, {})
                    invoice_ids = bf.get('invoice_ids') or []
                    if invoice_ids:
                        src = source_invoice_map.get(invoice_ids[0], {})
                        if src:
                            trace_invoice_map[move_id_key] = src
            except Exception as e:
                print(f"[WARN] No se pudo calcular trazabilidad por bill_form_id: {e}")

        # ---------- 2) Fallback por numero de letra ----------
        boe_numbers = {
            str(m.get('l10n_latam_boe_number')).strip()
            for m in move_map.values()
            if self._has_value(m.get('l10n_latam_boe_number'))
        }
        if not boe_numbers:
            return trace_invoice_map

        try:
            boe_candidates = self.repository.search_read(
                'account.move',
                [
                    ('move_type', '=', 'out_bill'),
                    ('l10n_latam_boe_number', 'in', list(boe_numbers))
                ],
                [
                    'id', 'name', 'state', 'move_type', 'l10n_latam_boe_number', 'bill_form_id',
                    'partner_id', 'amount_total', 'invoice_origin', 'invoice_payment_term_id',
                    'invoice_user_id', 'sales_channel_id', 'sale_type_id', 'team_id',
                    'bill_form_invoices_order_sales_line_commercial_zone_id'
                ],
                limit=10000
            ) or []

            candidate_bill_form_ids = {
                self._m2o_id(m.get('bill_form_id'))
                for m in boe_candidates
                if self._m2o_id(m.get('bill_form_id'))
            }
            candidate_bill_form_map = {}
            candidate_source_invoice_map = {}
            if candidate_bill_form_ids:
                candidate_bill_forms = self._read_in_batches(
                    'account.bill.form',
                    list(candidate_bill_form_ids),
                    ['id', 'invoice_ids'],
                    batch_size=300
                )
                candidate_bill_form_map = {bf['id']: bf for bf in candidate_bill_forms}
                candidate_source_ids = set()
                for bf in candidate_bill_forms:
                    candidate_source_ids.update(bf.get('invoice_ids') or [])
                if candidate_source_ids:
                    candidate_sources = self._read_in_batches(
                        'account.move',
                        list(candidate_source_ids),
                        [
                            'id', 'name', 'state', 'move_type', 'partner_id', 'amount_total',
                            'invoice_origin', 'invoice_payment_term_id', 'invoice_user_id',
                            'sales_channel_id', 'sale_type_id', 'team_id',
                            'bill_form_invoices_order_sales_line_commercial_zone_id'
                        ],
                        batch_size=300
                    )
                    candidate_source_invoice_map = {inv['id']: inv for inv in candidate_sources}

            boe_best_source = {}
            for cand in boe_candidates:
                boe = str(cand.get('l10n_latam_boe_number') or '').strip()
                if not boe:
                    continue

                src = cand
                bf_id = self._m2o_id(cand.get('bill_form_id'))
                if bf_id:
                    bf = candidate_bill_form_map.get(bf_id, {})
                    inv_ids = bf.get('invoice_ids') or []
                    if inv_ids:
                        src = candidate_source_invoice_map.get(inv_ids[0], cand)

                score_fields = [
                    'invoice_payment_term_id',
                    'sales_channel_id',
                    'sale_type_id',
                    'invoice_user_id',
                    'invoice_origin',
                    'bill_form_invoices_order_sales_line_commercial_zone_id',
                    'team_id',
                ]
                score = sum(1 for f in score_fields if self._has_value(src.get(f)))
                if src.get('move_type') == 'out_invoice':
                    score += 2
                if self._m2o_id(cand.get('bill_form_id')):
                    score += 1

                prev = boe_best_source.get(boe)
                if not prev or score > prev['score']:
                    boe_best_source[boe] = {'score': score, 'src': src}

            for move_id_key, move_data in move_map.items():
                if move_id_key in trace_invoice_map:
                    continue
                boe = str(move_data.get('l10n_latam_boe_number') or '').strip()
                best = boe_best_source.get(boe)
                if best and best.get('src'):
                    trace_invoice_map[move_id_key] = best['src']
        except Exception as e:
            print(f"[WARN] No se pudo calcular trazabilidad por numero de letra: {e}")

        return trace_invoice_map
    
    def get_filter_options(self, start_date=None, end_date=None, customer=None,
                           account_codes=None, sales_channel_id=None, cutoff_date=None,
                           include_reconciled=False):
        """
        Obtiene opciones para filtros (canales de venta, tipos de documento).
        
        Returns:
            dict: Diccionario con las opciones de filtros
        """
        try:
            print("[INFO] Obteniendo opciones de filtros...")
            
            if not self.repository.is_connected():
                print("[ERROR] No hay conexión a Odoo disponible")
                return {'sales_channels': [], 'document_types': [], 'sub_channels': [], 'payment_methods': []}
            
            # Obtener canales de venta
            sales_channels = []
            try:
                # Buscar canales activos
                channels = self.repository.search_read(
                    'agr.sales.channel',
                    [],
                    ['id', 'name'],
                    limit=200
                )
                sales_channels = [
                    {'id': ch['id'], 'name': ch.get('name', '')}
                    for ch in channels
                ]
                sales_channels.sort(key=lambda x: x['name'])
            except Exception as e:
                print(f"[WARN] No se pudo obtener canales de venta: {e}")
            
            # Obtener sub canales desde agr.credit.customer + defaults
            sub_channels = []
            try:
                sub_channel_set = {"NACIONAL", "INTERNACIONAL"}
                credit_rows = self.repository.search_read(
                    'agr.credit.customer',
                    [],
                    ['sub_channel_id'],
                    limit=5000
                )
                for row in credit_rows:
                    sub = row.get('sub_channel_id')
                    if isinstance(sub, list) and len(sub) >= 2 and sub[1]:
                        sub_channel_set.add(str(sub[1]).strip())
                sub_channels = [{'value': name, 'name': name} for name in sorted(sub_channel_set)]
            except Exception as e:
                print(f"[WARN] No se pudo obtener sub canales: {e}")

            # Obtener tipos de documento LATAM
            document_types = []
            try:
                allowed_doc_types = ['Boleta', 'Factura', 'Nota de Crédito', 'Nota de Débito']
                
                doc_types = self.repository.search_read(
                    'l10n_latam.document.type',
                    [],
                    ['id', 'name'],
                    limit=200
                )
                
                # Filtrar solo los tipos de documento permitidos con registros.
                for doc in doc_types:
                    doc_name = doc.get('name', '')
                    if any(allowed_type.lower() in doc_name.lower() for allowed_type in allowed_doc_types):
                        try:
                            doc_domain = self._build_report_domain(
                                start_date=start_date,
                                end_date=end_date,
                                customer=customer,
                                account_codes=account_codes,
                                sales_channel_id=sales_channel_id,
                                doc_type_id=doc['id'],
                                cutoff_date=cutoff_date,
                                include_reconciled=include_reconciled
                            )
                            doc_count = self.repository.search_count('account.move.line', doc_domain)
                        except Exception:
                            doc_count = 0

                        if doc_count > 0:
                            document_types.append({
                                'id': doc['id'],
                                'name': doc_name
                            })
                
                document_types.sort(key=lambda x: x['name'])
            except Exception as e:
                print(f"[WARN] No se pudo obtener tipos de documento: {e}")
            
            # Obtener métodos de pago siguiendo la ruta move_id/order_id/tag_ids:
            # 1. Buscar órdenes de venta que tengan etiquetas asignadas
            # 2. Leer los registros crm.tag de esos IDs únicos
            # Así solo se muestran etiquetas realmente usadas en órdenes de venta.
            payment_methods = []
            try:
                order_tag_rows = self.repository.search_read(
                    'sale.order',
                    [('tag_ids', '!=', False)],
                    ['tag_ids'],
                    limit=5000
                )
                tag_ids_set = set()
                for row in order_tag_rows:
                    for tid in (row.get('tag_ids') or []):
                        tag_ids_set.add(tid)
                if tag_ids_set:
                    tag_records = self.repository.read('crm.tag', list(tag_ids_set), ['id', 'name'])
                    payment_methods = [
                        {'id': t['id'], 'name': t.get('name', '')}
                        for t in tag_records if t.get('name')
                    ]
                    payment_methods.sort(key=lambda x: x['name'])
            except Exception as e:
                print(f"[WARN] No se pudo obtener métodos de pago (move_id/order_id/tag_ids): {e}")

            print(f"[OK] Filtros obtenidos: {len(sales_channels)} canales, {len(document_types)} tipos de documento, {len(sub_channels)} sub canales, {len(payment_methods)} métodos de pago")

            return {
                'sales_channels': sales_channels,
                'document_types': document_types,
                'sub_channels': sub_channels,
                'payment_methods': payment_methods,
            }
            
        except Exception as e:
            print(f"[ERROR] Error obteniendo opciones de filtros: {e}")
            import traceback
            traceback.print_exc()
            return {'sales_channels': [], 'document_types': [], 'sub_channels': [], 'payment_methods': []}
    
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
    def _parse_account_codes(account_codes):
        """
        Normaliza los códigos de cuenta ingresados por el usuario.
        Si no se envía nada, usa el set por defecto del módulo de cobranzas.
        """
        if account_codes and str(account_codes).strip():
            parsed = [code.strip() for code in str(account_codes).split(',') if code.strip()]
            if parsed:
                return parsed
        return ['122', '1212', '123', '1312', '132', '13']

    @staticmethod
    def _collapse_1212_lines(rows: list, today) -> list:
        """
        Regla de negocio contable por cuenta contable:

        - Cuenta 1212*  → COLAPSA cuotas en UNA línea por factura (monto unificado).
                          Una factura con 5 cuotas aparece como 1 registro con
                          el total consolidado.
        - Cuenta 123*   → MANTIENE cada línea/letra individual tal como viene de Odoo.
                          El desdoblamiento ya existe en la fuente (una línea por letra).
        - Resto          → Sin cambio.
        """
        from collections import defaultdict
        from datetime import datetime as _datetime

        rows_1212: list = []
        rows_other: list = []

        for row in rows:
            code = str(row.get('account_id/code') or '')
            if code.startswith('1212'):
                rows_1212.append(row)
            else:
                rows_other.append(row)

        if not rows_1212:
            return rows

        # --- Agrupar 1212 por clave de factura ---
        grouped: dict = defaultdict(list)
        for row in rows_1212:
            key = (
                row.get('move_name')
                or row.get('account.move/name')
                or str(row.get('payment_state', '')) + str(id(row))
            )
            grouped[key].append(row)

        # Campos que se suman entre cuotas de la misma factura
        sum_fields = [
            'debit', 'credit', 'balance',
            'amount_currency', 'amount_residual_currency',
            'amount_residual_historical', 'paid_after_cutoff', 'paid_before_cutoff',
        ]

        collapsed: list = []
        for _key, cuotas in grouped.items():
            base = dict(cuotas[0])  # cabecera: campos de factura (idénticos por cuota)

            for f in sum_fields:
                base[f] = sum(float(c.get(f) or 0.0) for c in cuotas)

            # date_maturity efectivo:
            #   - Si hay cuotas vencidas → MIN (primera cuota vencida)
            #   - Si todas vigentes   → MAX (próximo vencimiento)
            maturities = []
            for c in cuotas:
                dm = c.get('date_maturity')
                if dm:
                    try:
                        d = (
                            dm if not isinstance(dm, str)
                            else _datetime.strptime(dm[:10], '%Y-%m-%d').date()
                        )
                        maturities.append(d)
                    except (ValueError, TypeError):
                        pass

            overdue_dates = [d for d in maturities if d < today]
            effective_maturity = (
                min(overdue_dates) if overdue_dates
                else (max(maturities) if maturities else None)
            )
            base['date_maturity'] = str(effective_maturity) if effective_maturity else ''

            # Recalcular campos derivados desde el vencimiento efectivo
            from app.core.calculators import calcular_dias_vencido, clasificar_antiguedad
            dias = calcular_dias_vencido(base['date_maturity'], today) if base['date_maturity'] else 0
            base['dias_vencido'] = dias
            base['estado_deuda'] = 'VENCIDO' if dias > 0 else 'VIGENTE'
            base['antiguedad'] = clasificar_antiguedad(max(0, dias))

            if base.get('estado_historico') not in ('', None):
                base['estado_historico'] = (
                    'PAGADA' if float(base.get('amount_residual_historical') or 0.0) <= 0
                    else 'NO PAGADA'
                )

            base['_cuotas_colapsadas'] = len(cuotas)
            collapsed.append(base)

        return collapsed + rows_other

    @staticmethod
    def _aplica_corte_historico(
        fecha_emision: str,
        fecha_pago,
        amount_residual_historical: float,
        cutoff_date: str,
        include_reconciled: bool = False,
    ) -> bool:
        """
        Regla de Corte Histórico.

        Un registro se INCLUYE en el reporte si cumple AMBAS condiciones:

          1. fecha_emision <= fecha_corte
             El documento fue emitido (contabilizado) antes o en la fecha de corte.

          2. fecha_pago IS NULL  (nunca pagado)
             OR fecha_pago > fecha_corte  (se pagó DESPUÉS del corte)

        Equivalencias contables:
          - fecha_emision  = account.move.line.date  (campo 'date' de la línea)
          - fecha_pago     = MAX(account.partial.reconcile.max_date) de la línea
          - "pagado al corte" ↔ amount_residual_historical <= 0

        Args:
            fecha_emision (str): Fecha contable de la línea 'YYYY-MM-DD'.
            fecha_pago (str | None): Fecha del último pago/conciliación.
            amount_residual_historical (float): Saldo reconstruido a la fecha de corte.
            cutoff_date (str): Fecha de corte 'YYYY-MM-DD'.
            include_reconciled (bool): Si True, incluye también los documentos ya
                pagados al corte (útil para auditorías históricas completas).

        Returns:
            bool: True si el registro debe aparecer en el reporte de corte.
        """
        # Condición 1: emitido antes o en la fecha de corte
        # (ya garantizado por el domain SQL, pero se verifica como salvaguarda)
        if fecha_emision and fecha_emision > cutoff_date:
            return False

        # Condición 2: no estaba pagado al corte
        # "pagado al corte" = conciliado antes/en corte Y sin saldo residual histórico
        pagado_al_corte = (
            fecha_pago is not None
            and fecha_pago <= cutoff_date
            and amount_residual_historical <= 0
        )

        if pagado_al_corte:
            # Excluir si el caller no pide ver documentos ya pagados al corte
            return include_reconciled

        return True

    def _build_report_domain(self, start_date=None, end_date=None, customer=None,
                            account_codes=None, sales_channel_id=None, doc_type_id=None,
                            sub_channel=None, date_cutoff_start=None,
                            cutoff_date=None, include_reconciled=False, doc_number=None):
        """
        Construye el domain de Odoo para filtrar líneas de movimiento.
        Método auxiliar para evitar duplicación de código.
        
        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
            customer (str): Nombre del cliente
            account_codes (str): Códigos de cuenta separados por coma
            sales_channel_id (int): ID del canal de ventas
            doc_type_id (int): ID del tipo de documento
            sub_channel (str): Sub canal (se aplica en post-proceso)
        
        Returns:
            list: Domain de Odoo listo para usar en búsquedas
        """
        account_code_list = self._parse_account_codes(account_codes)

        # Dominio base
        domain = [
            ('account_id.reconcile', '=', True),
            ('parent_state', 'in', (
                'posted',
                'portfolio',
                'accepted',
                'collection',
                'discount',
                'warranty',
                'disbursed',
                'protested'
            ))
        ]

        # Filtro dinámico por códigos de cuenta
        if account_code_list:
            account_terms = [('account_id.code', '=like', f'{code}%') for code in account_code_list]
            if len(account_terms) == 1:
                domain.append(account_terms[0])
            else:
                domain.extend((['|'] * (len(account_terms) - 1)) + account_terms)
        
        # Filtros adicionales / histórico
        if cutoff_date:
            # Foto histórica: sólo líneas contabilizadas hasta la fecha de corte.
            domain.append(('date', '<=', cutoff_date))
            # Límite inferior: solo si el usuario especificó una Fecha Origen (date_cutoff_start).
            # Si no se envía nada, no se limita (permite traer años anteriores como 2025, 2024, etc.).
            if date_cutoff_start and str(date_cutoff_start).strip():
                domain.append(('date', '>=', str(date_cutoff_start).strip()))
        else:
            domain.append(('amount_residual', '!=', 0))
            if start_date:
                domain.append(('date', '>=', start_date))
            if end_date:
                domain.append(('date', '<=', end_date))
            if not include_reconciled:
                domain.append(('reconciled', '=', False))

        # Excluir la cuenta contable 1239001 (Saldos iniciales - no forma parte de CxC activa)
        domain.append(('account_id.code', '!=', '1239001'))

        if customer:
            domain.append(('partner_id.name', 'ilike', customer))
        if sales_channel_id:
            domain.append(('move_id.sales_channel_id', '=', sales_channel_id))
            if doc_type_id:
                domain.append(('move_id.l10n_latam_document_type_id', '=', doc_type_id))
        elif doc_type_id:
            domain.append(('move_id.l10n_latam_document_type_id', '=', doc_type_id))

        if doc_number and str(doc_number).strip():
            q = str(doc_number).strip()
            # Busca por número de factura/documento O por número de letra (BOE)
            domain.extend([
                '|',
                ('move_id.name', 'ilike', q),
                ('move_id.l10n_latam_boe_number', 'ilike', q),
            ])

        return domain
    
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
                         account_codes=None, sales_channel_id=None, doc_type_id=None,
                         sub_channel=None, date_cutoff_start=None, payment_method=None,
                         cutoff_date=None, include_reconciled=False, doc_number=None):
        """
        Obtener líneas de reporte de CxC siguiendo la cadena de relaciones.

        Aplica regla de negocio contable por cuenta:
        - Cuenta 1212*: Colapsa cuotas en UNA línea por factura (monto unificado).
        - Cuenta 123*:  Mantiene línea individual por letra (ya desglosado en origen).

        Args:
            start_date (str): Fecha inicial
            end_date (str): Fecha final
            customer (str): Nombre de cliente a filtrar
            limit (int): Límite de registros
            account_codes (str): Códigos de cuenta separados por coma
            sales_channel_id (int): ID del canal de ventas
            doc_type_id (int): ID del tipo de documento
            sub_channel (str): Sub canal
            doc_number (str): Nro de documento/comprobante para búsqueda exacta

        Returns:
            list: Líneas de reporte CxC
        """
        try:
            print("[INFO] Obteniendo líneas de reporte CxC...")
            
            if not self.repository.is_connected():
                print("[ERROR] No hay conexión a Odoo disponible")
                return []
            
            line_domain = self._build_report_domain(
                start_date=start_date,
                end_date=end_date,
                customer=customer,
                account_codes=account_codes,
                sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id,
                sub_channel=sub_channel,
                date_cutoff_start=date_cutoff_start,
                cutoff_date=cutoff_date,
                include_reconciled=include_reconciled,
                doc_number=doc_number,
            )

            # Campos a extraer
            line_fields = [
                'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
                'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
                'debit', 'credit', 'balance', 'parent_state', 'matched_debit_ids', 'matched_credit_ids',
            ]
            
            # Si limit <= 0 o None, traer todos los registros para análisis.
            effective_limit = limit if limit and limit > 0 else None
            # Mismo orden que CollectionsSupabaseProvider (ORDER BY date DESC, id DESC)
            # para que escenarios con limit produzcan el mismo subconjunto de líneas.
            lines = self.repository.search_read(
                'account.move.line', line_domain, line_fields,
                limit=effective_limit,
                order='date desc, id desc',
            )
            
            print(f"[OK] Obtenidas {len(lines)} líneas de asiento contable")
            
            if not lines:
                return []
            
            # Extraer IDs únicos
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            account_ids = list(set([l['account_id'][0] for l in lines if l.get('account_id')]))
            
            # 3. Obtener datos relacionados de forma secuencial por lotes (más estable para XML-RPC)
            move_map = {}
            partner_map = {}
            account_map = {}
            credit_map = {}
            reconciliation_map = {}

            if move_ids:
                move_fields = [
                    'id', 'name', 'state', 'move_type', 'bill_form_id',
                    'payment_state', 'invoice_date', 'date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'amount_residual_with_retention', 'amount_residual_signed', 'currency_id',
                    'l10n_latam_boe_number',
                    'ref', 'invoice_payment_term_id', 'invoice_user_id',
                    'sales_channel_id', 'sale_type_id', 'team_id',
                    'bill_form_invoices_order_sales_line_commercial_zone_id',
                    'order_id',
                ]
                moves = self._read_in_batches('account.move', move_ids, move_fields, batch_size=300)
                move_map = {m['id']: m for m in moves}

            trace_invoice_map = self._build_trace_invoice_map(move_map)

            # Construir mapa de órdenes de venta para obtener sub_channel_id (move_id/order_id/sub_channel_id)
            order_map = {}
            order_ids_set = set()
            for m in move_map.values():
                oid = m.get('order_id')
                if isinstance(oid, list) and oid and oid[0]:
                    order_ids_set.add(oid[0])
            if order_ids_set:
                try:
                    orders = self._read_in_batches('sale.order', list(order_ids_set), ['id', 'sub_channel_id', 'tag_ids'], batch_size=300)
                    order_map = {o['id']: o for o in orders}
                except Exception as e:
                    print(f"[WARN] No se pudo obtener sale.order para sub_channel_id: {e}")

            # Mapa de etiquetas (tag_ids → nombre) para método de pago
            tag_map = {}
            try:
                all_tag_ids = set()
                for o in order_map.values():
                    for tid in (o.get('tag_ids') or []):
                        all_tag_ids.add(tid)
                if all_tag_ids:
                    tags = self.repository.read('crm.tag', list(all_tag_ids), ['id', 'name'])
                    tag_map = {t['id']: t.get('name', '') for t in tags}
            except Exception as e:
                print(f"[WARN] No se pudo obtener nombres de etiquetas (crm.tag): {e}")

            if partner_ids:
                partner_fields = [
                    'id', 'name', 'vat', 'state_id', 'l10n_pe_district',
                    'country_code', 'country_id', 'groups_ids'
                ]
                partners = self._read_in_batches('res.partner', partner_ids, partner_fields, batch_size=300)
                partner_map = {p['id']: p for p in partners}

            if account_ids:
                accounts = self._read_in_batches(
                    'account.account',
                    account_ids,
                    ['id', 'code', 'name', 'currency_id'],
                    batch_size=300
                )
                account_map = {a['id']: a for a in accounts}

            if partner_ids:
                try:
                    credit_customers = self._search_read_in_batches(
                        'agr.credit.customer',
                        'partner_id',
                        partner_ids,
                        ['partner_id', 'partner_groups_ids', 'sub_channel_id'],
                        batch_size=200
                    )
                    credit_map = {cc['partner_id'][0]: cc for cc in credit_customers if cc.get('partner_id')}
                except Exception as e:
                    print(f"[WARN] No se pudo obtener agr.credit.customer: {e}")

            if cutoff_date:
                reconciliation_map = self._get_reconciliation_amounts(lines, cutoff_date)

            # Obtener nombres de línea comercial desde agr.credit.customer.partner_groups_ids
            partner_groups_map = {}
            credit_group_ids = set()
            for credit_data in credit_map.values():
                for gid in credit_data.get('partner_groups_ids') or []:
                    credit_group_ids.add(gid)

            if credit_group_ids:
                try:
                    group_records = self.repository.read(
                        'agr.groups',
                        list(credit_group_ids),
                        ['id', 'name']
                    )
                    group_name_map = {g['id']: g.get('name', '') for g in group_records}
                    for partner_id_key, credit_data in credit_map.items():
                        names = [group_name_map[gid] for gid in credit_data.get('partner_groups_ids') or [] if gid in group_name_map]
                        partner_groups_map[partner_id_key] = ', '.join(names)
                except Exception as e:
                    print(f"[WARN] No se pudieron obtener los nombres de línea comercial: {e}")
            
            # Combinar datos
            rows = []
            today = datetime.today().date()
            
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


                source_move_base = trace_invoice_map.get(move_id, {})

                account_code = str(account.get('code') or '')
                is_letters_account = account_code.startswith('123')
                source_move = {}
                if is_letters_account and source_move_base:
                    source_move = source_move_base
                
                # Determinar Sub Canal desde move_id/order_id/sub_channel_id
                order_id_val = move.get('order_id') or source_move.get('order_id')
                if isinstance(order_id_val, list) and order_id_val and order_id_val[0]:
                    order = order_map.get(order_id_val[0], {})
                    sub_channel_raw = m2o_name(order.get('sub_channel_id'))
                else:
                    sub_channel_raw = ''
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

                if sub_channel and str(sub_channel).strip():
                    if sub_channel_final.strip().upper() != str(sub_channel).strip().upper():
                        continue

                # Determinar Método de Pago desde sale.order.tag_ids
                order_for_tags = order_map.get(order_id_val[0], {}) if isinstance(order_id_val, list) and order_id_val else {}
                order_tag_ids = order_for_tags.get('tag_ids') or []
                payment_method_display = ', '.join(
                    tag_map[tid] for tid in order_tag_ids if tid in tag_map
                )

                # Filtro post-proceso por método de pago (ID de crm.tag)
                if payment_method and str(payment_method).strip():
                    try:
                        pm_id = int(payment_method)
                        if pm_id not in order_tag_ids:
                            continue
                    except (ValueError, TypeError):
                        pass

                # Determinar grupos del partner
                partner_groups_display = partner_groups_map.get(partner_id, '')

                # Calcular días de vencimiento
                date_maturity = line.get('date_maturity', '')
                dias_vencido = calcular_dias_vencido(date_maturity, today) if date_maturity else 0

                # Clasificar antigüedad
                antiguedad = clasificar_antiguedad(max(0, dias_vencido))
                
                # Estado de deuda
                estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'

                # Conciliaciones / histórico
                rec_info = reconciliation_map.get(line['id'], {})
                reconcile_date = rec_info.get('max_date')
                paid_after_cutoff = float(rec_info.get('paid_after', 0.0) or 0.0)
                paid_before_cutoff = float(rec_info.get('paid_before', 0.0) or 0.0)

                current_residual = abs(line.get('amount_residual', 0.0) or 0.0)
                amount_residual_historical = current_residual
                estado_historico = ''
                if cutoff_date:
                    # Reconstruir saldo al corte: residual actual + lo que se pagó DESPUÉS del corte
                    amount_residual_historical = current_residual + paid_after_cutoff
                    # Forzar cero cuando está completamente conciliado antes/en el corte
                    if reconcile_date and reconcile_date <= cutoff_date and amount_residual_historical <= 0:
                        amount_residual_historical = 0.0

                    estado_historico = 'PAGADA' if amount_residual_historical <= 0 else 'NO PAGADA'

                    # Regla de Corte Histórico explícita:
                    #   fecha_emision <= fecha_corte  AND
                    #   (fecha_pago IS NULL  OR  fecha_pago > fecha_corte)
                    fecha_emision_linea = line.get('date') or move.get('invoice_date') or ''
                    if not self._aplica_corte_historico(
                        fecha_emision=fecha_emision_linea,
                        fecha_pago=reconcile_date,
                        amount_residual_historical=amount_residual_historical,
                        cutoff_date=cutoff_date,
                        include_reconciled=include_reconciled,
                    ):
                        continue
                
                row = {
                    'payment_state': move.get('payment_state', ''),
                    'move_id/payment_state': move.get('payment_state', ''),
                    'payment_state_display': PAYMENT_STATE_LABELS_ES.get(
                        move.get('payment_state', ''), move.get('payment_state', '')
                    ),
                    'parent_state': line.get('parent_state', ''),
                    'move_id/parent_state': line.get('parent_state', ''),
                    'move_id/state': DOCUMENT_STATE_LABELS_ES.get(move.get('state'), move.get('state') or ''),
                    'state': DOCUMENT_STATE_LABELS_ES.get(move.get('state'), move.get('state') or ''),
                    'invoice_date': move.get('invoice_date', ''),
                    'move_id/invoice_date': move.get('invoice_date', ''),
                    'account.move/invoice_date': move.get('date', ''),
                    'l10n_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'account.move/l10n_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'move_name': move.get('name', ''),
                    'account.move/name': move.get('name', ''),
                    'l10n_latam_boe_number': move.get('l10n_latam_boe_number', ''),
                    'account.move/l10n_latam_boe_number': move.get('l10n_latam_boe_number', ''),
                    'invoice_origin': move.get('invoice_origin', '') or source_move.get('invoice_origin', ''),
                    'account.move/invoice_origin': move.get('invoice_origin', '') or source_move.get('invoice_origin', ''),
                    'account_id/code': account.get('code', ''),
                    'account_id/name': account.get('name', ''),
                    'partner_vat': partner.get('vat', ''),
                    'partner_name': partner.get('name', ''),
                    'partner_id': partner.get('name', ''), # Alias para compatibilidad
                    'patner_id/vat': partner.get('vat', ''), # Alias con typo para compatibilidad
                    'patner_id': partner.get('name', ''), # Alias con typo para compatibilidad
                    'partner_state': m2o_name(partner.get('state_id')),
                    'partner_district': partner.get('l10n_pe_district', ''),
                    'partner_country_code': country_code,
                    'partner_country_name': m2o_name(partner.get('country_id')),
                    'patner_id/state_id': m2o_name(partner.get('state_id')), # Alias legacy para exportación
                    'patner_id/l10n_pe_district': partner.get('l10n_pe_district', ''), # Alias legacy
                    'patner_id/country_code': country_code, # Alias legacy
                    'patner_id/country_id': m2o_name(partner.get('country_id')), # Alias legacy
                    'currency_id': m2o_name(account.get('currency_id') or line.get('currency_id') or move.get('currency_id')),
                    'account_id/currency_id': m2o_name(account.get('currency_id') or line.get('currency_id') or move.get('currency_id')),
                    'amount_total': move.get('amount_total', 0.0),
                    'account.move/amount_total': move.get('amount_total', 0.0),
                    'amount_residual_with_retention': move.get('amount_residual_with_retention', move.get('amount_residual', 0.0)),
                    'amount_residual_signed': move.get('amount_residual_signed', 0.0),
                    'account.move/amount_residual': move.get('amount_residual', 0.0),
                    'amount_currency': line.get('amount_currency', 0.0),
                    'amount_residual_currency': line.get('amount_residual', 0.0),
                    'amount_residual_historical': amount_residual_historical,
                    'paid_after_cutoff': paid_after_cutoff,
                    'paid_before_cutoff': paid_before_cutoff,
                    'debit': line.get('debit', 0.0) or 0.0,
                    'credit': line.get('credit', 0.0) or 0.0,
                    'balance': line.get('balance', 0.0) or 0.0,
                    'date': line.get('date', ''),
                    'date_maturity': date_maturity,
                    'invoice_date_due': move.get('invoice_date_due', ''),
                    'account.move/invoice_date_due': move.get('invoice_date_due', ''),
                    'ref': move.get('ref', ''),
                    'invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')) or m2o_name(source_move.get('invoice_payment_term_id')),
                    'account.move/invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')) or m2o_name(source_move.get('invoice_payment_term_id')),
                    'name': line.get('name', ''),
                    'account.move.line/name': line.get('name', ''),
                    'invoice_user_name': m2o_name(move.get('invoice_user_id')) or m2o_name(source_move.get('invoice_user_id')),
                    'account.move/invoice_user_id': m2o_name(move.get('invoice_user_id')) or m2o_name(source_move.get('invoice_user_id')),
                    # Canal de venta: prioridad 1 sales_channel_id (move → source_move), prioridad 2 bill_form_invoices_order_channel_id
                    'sales_channel_name': (
                        m2o_name(move.get('sales_channel_id'))
                        or m2o_name(source_move.get('sales_channel_id'))
                        or m2o_name(move.get('bill_form_invoices_order_channel_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_channel_id'))
                    ),
                    'account.move/sales_channel_id': (
                        m2o_name(move.get('sales_channel_id'))
                        or m2o_name(source_move.get('sales_channel_id'))
                        or m2o_name(move.get('bill_form_invoices_order_channel_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_channel_id'))
                    ),
                    # Tipo de venta: prioridad 1 sale_type_id (move → source_move), prioridad 2 bill_form_invoices_order_sales_type_id
                    'sales_type_name': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),
                    'account.move/sales_type_id': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),
                    'account.move/sale_type_id': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),
                    'linea_comercial': (
                        m2o_name(move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(move.get('team_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(source_move.get('team_id'))
                    ),
                    'account.move/linea_comercial': (
                        m2o_name(move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(move.get('team_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(source_move.get('team_id'))
                    ),
                    'team_name': m2o_name(move.get('team_id')) or m2o_name(source_move.get('team_id')),
                    'move_id/invoice_user_id': m2o_name(move.get('invoice_user_id')) or m2o_name(source_move.get('invoice_user_id')), # Alias legacy para exportación
                    'move_id/sales_channel_id': (
                        m2o_name(move.get('sales_channel_id'))
                        or m2o_name(source_move.get('sales_channel_id'))
                        or m2o_name(move.get('bill_form_invoices_order_channel_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_channel_id'))
                    ), # Alias legacy
                    'move_id/sales_type_id': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ), # Alias legacy
                    'move_id/payment_state': move.get('payment_state', ''), # Alias legacy
                    'team_id': m2o_name(move.get('team_id')) or m2o_name(source_move.get('team_id')), # Alias legacy para exportación
                    'partner_groups': partner_groups_display,
                    'grupo_comercial': partner_groups_display,
                    'agr.credit.customer/patner_groups_ids': partner_groups_display,
                    'agr.credit.customer/partner_groups_ids': partner_groups_display,
                    'sub_channel_id': sub_channel_final,
                    'agr.credit.customer/sub_channel_id': sub_channel_final,
                    'payment_method': payment_method_display,
                    'move_id/order_id/tag_ids': payment_method_display,
                    # Campos calculados
                    'dias_vencido': dias_vencido,
                    'estado_deuda': estado_deuda,
                    'estado_historico': estado_historico,
                    'antiguedad': antiguedad,
                    'reconciliation_date': reconcile_date,
                }

                rows.append(row)

            # Regla de negocio contable: 1212 → colapsar cuotas; 123 → mantener individual
            rows = self._collapse_1212_lines(rows, today)

            print(f"[OK] Procesadas {len(rows)} líneas de CxC con TODOS los campos")
            return rows
            
        except Exception as e:
            print(f"[ERROR] Error al obtener las líneas de reporte CxC: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_report_lines_paginated(self, page=1, per_page=50, **kwargs):
        """
        Obtiene líneas de reporte con paginación eficiente en Odoo.
        VERSIÓN OPTIMIZADA - Solo trae los registros de la página solicitada.
        
        Args:
            page (int): Número de página (1-indexed)
            per_page (int): Registros por página
            **kwargs: Filtros (start_date, end_date, customer, account_codes, sales_channel_id, doc_type_id)
        
        Returns:
            dict: {
                'data': [...],
                'total_count': 1234,
                'page': 1,
                'per_page': 50,
                'total_pages': 25,
                'has_more': True
            }
        """
        try:
            print(f"[INFO] Obteniendo página {page} (per_page={per_page})")
            
            if not self.repository.is_connected():
                raise ValueError("No hay conexión a Odoo disponible")
            
            # Extraer filtros
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            customer = kwargs.get('customer')
            account_codes = kwargs.get('account_codes')
            sales_channel_id = kwargs.get('sales_channel_id')
            doc_type_id = kwargs.get('doc_type_id')
            sub_channel = kwargs.get('sub_channel')
            date_cutoff_start = kwargs.get('date_cutoff_start')
            payment_method = kwargs.get('payment_method')
            cutoff_date = kwargs.get('cutoff_date')
            include_reconciled = kwargs.get('include_reconciled', False)

            # Construir domain usando el método auxiliar (ahora incluye filtro inteligente)
            line_domain = self._build_report_domain(
                start_date=start_date,
                end_date=end_date,
                customer=customer,
                account_codes=account_codes,
                sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id,
                sub_channel=sub_channel,
                date_cutoff_start=date_cutoff_start,
                cutoff_date=cutoff_date,
                include_reconciled=include_reconciled
            )
            
            # 1. Obtener TOTAL de registros (sin traer datos)
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
                'debit', 'credit', 'balance', 'parent_state', 'matched_debit_ids', 'matched_credit_ids'
            ]
            
            lines = self.repository.search_read(
                'account.move.line',
                line_domain,
                line_fields,
                limit=per_page,
                offset=offset,
                order='date desc, id desc',
            )
            
            print(f"[OK] Obtenidos {len(lines)} registros de {total_count} totales")
            
            if not lines:
                return {
                    'data': [],
                    'total_count': total_count,
                    'page': page,
                    'per_page': per_page,
                    'total_pages': (total_count + per_page - 1) // per_page,
                    'has_more': False
                }
            
            # 4. Procesar líneas con datos relacionados
            move_ids = list(set([l['move_id'][0] for l in lines if l.get('move_id')]))
            partner_ids = list(set([l['partner_id'][0] for l in lines if l.get('partner_id')]))
            account_ids = list(set([l['account_id'][0] for l in lines if l.get('account_id')]))

            move_map = {}
            partner_map = {}
            account_map = {}
            credit_map = {}
            reconciliation_map = {}

            if move_ids:
                move_fields = [
                    'id', 'name', 'state', 'move_type', 'bill_form_id',
                    'payment_state', 'invoice_date', 'date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'amount_residual_with_retention', 'amount_residual_signed', 'currency_id',
                    'l10n_latam_boe_number', 'ref', 'invoice_payment_term_id', 'invoice_user_id',
                    'sales_channel_id', 'sale_type_id', 'team_id',
                    'bill_form_invoices_order_sales_line_commercial_zone_id',
                    'order_id',
                ]
                moves = self._read_in_batches('account.move', move_ids, move_fields, batch_size=300)
                move_map = {m['id']: m for m in moves}

            trace_invoice_map = self._build_trace_invoice_map(move_map)

            # Construir mapa de órdenes de venta para obtener sub_channel_id (move_id/order_id/sub_channel_id)
            order_map = {}
            order_ids_set = set()
            for m in move_map.values():
                oid = m.get('order_id')
                if isinstance(oid, list) and oid and oid[0]:
                    order_ids_set.add(oid[0])
            if order_ids_set:
                try:
                    orders = self._read_in_batches('sale.order', list(order_ids_set), ['id', 'sub_channel_id', 'tag_ids'], batch_size=300)
                    order_map = {o['id']: o for o in orders}
                except Exception as e:
                    print(f"[WARN] No se pudo obtener sale.order para sub_channel_id: {e}")

            # Mapa de etiquetas (tag_ids → nombre) para método de pago
            tag_map = {}
            try:
                all_tag_ids = set()
                for o in order_map.values():
                    for tid in (o.get('tag_ids') or []):
                        all_tag_ids.add(tid)
                if all_tag_ids:
                    tags = self.repository.read('crm.tag', list(all_tag_ids), ['id', 'name'])
                    tag_map = {t['id']: t.get('name', '') for t in tags}
            except Exception as e:
                print(f"[WARN] No se pudo obtener nombres de etiquetas (crm.tag): {e}")

            if partner_ids:
                partner_fields = [
                    'id', 'name', 'vat', 'state_id', 'l10n_pe_district',
                    'country_code', 'country_id', 'groups_ids'
                ]
                partners = self._read_in_batches('res.partner', partner_ids, partner_fields, batch_size=300)
                partner_map = {p['id']: p for p in partners}

            if account_ids:
                accounts = self._read_in_batches(
                    'account.account',
                    account_ids,
                    ['id', 'code', 'name', 'currency_id'],
                    batch_size=300
                )
                account_map = {a['id']: a for a in accounts}

            if partner_ids:
                try:
                    credit_customers = self._search_read_in_batches(
                        'agr.credit.customer',
                        'partner_id',
                        partner_ids,
                        ['partner_id', 'partner_groups_ids', 'sub_channel_id'],
                        batch_size=200
                    )
                    for cred in credit_customers:
                        pid = cred['partner_id'][0] if isinstance(cred.get('partner_id'), list) else cred.get('partner_id')
                        if pid:
                            credit_map[pid] = cred
                except Exception as e:
                    print(f"[WARN] No se pudo obtener sub_channel_id: {e}")

            if cutoff_date:
                reconciliation_map = self._get_reconciliation_amounts(lines, cutoff_date)

            # Obtener nombres de línea comercial desde agr.credit.customer.partner_groups_ids
            partner_groups_map = {}
            credit_group_ids = set()
            for credit_data in credit_map.values():
                for gid in credit_data.get('partner_groups_ids') or []:
                    credit_group_ids.add(gid)

            if credit_group_ids:
                try:
                    group_records = self.repository.read(
                        'agr.groups',
                        list(credit_group_ids),
                        ['id', 'name']
                    )
                    group_name_map = {g['id']: g.get('name', '') for g in group_records}
                    for partner_id_key, credit_data in credit_map.items():
                        names = [group_name_map[gid] for gid in credit_data.get('partner_groups_ids') or [] if gid in group_name_map]
                        partner_groups_map[partner_id_key] = ', '.join(names)
                except Exception as e:
                    print(f"[WARN] No se pudieron obtener nombres de línea comercial: {e}")
            
            # Procesar líneas
            rows = []
            today = datetime.today().date()
            
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


                source_move_base = trace_invoice_map.get(move_id, {})

                account_code = str(account.get('code') or '')
                is_letters_account = account_code.startswith('123')
                source_move = {}
                if is_letters_account and source_move_base:
                    source_move = source_move_base
                
                # Determinar Sub Canal desde move_id/order_id/sub_channel_id
                order_id_val = move.get('order_id') or source_move.get('order_id')
                if isinstance(order_id_val, list) and order_id_val and order_id_val[0]:
                    order = order_map.get(order_id_val[0], {})
                    sub_channel_raw = m2o_name(order.get('sub_channel_id'))
                else:
                    sub_channel_raw = ''
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

                if sub_channel and str(sub_channel).strip():
                    if sub_channel_final.strip().upper() != str(sub_channel).strip().upper():
                        continue

                # Determinar Método de Pago desde sale.order.tag_ids
                order_for_tags = order_map.get(order_id_val[0], {}) if isinstance(order_id_val, list) and order_id_val else {}
                order_tag_ids = order_for_tags.get('tag_ids') or []
                payment_method_display = ', '.join(
                    tag_map[tid] for tid in order_tag_ids if tid in tag_map
                )

                # Filtro post-proceso por método de pago (ID de crm.tag)
                if payment_method and str(payment_method).strip():
                    try:
                        pm_id = int(payment_method)
                        if pm_id not in order_tag_ids:
                            continue
                    except (ValueError, TypeError):
                        pass

                partner_groups_display = partner_groups_map.get(partner_id, '')

                # Calcular días de vencimiento
                date_maturity = line.get('date_maturity', '')
                dias_vencido = calcular_dias_vencido(date_maturity, today) if date_maturity else 0

                # Clasificar antigüedad
                antiguedad = clasificar_antiguedad(max(0, dias_vencido))

                # Estado de deuda
                estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'

                rec_info = reconciliation_map.get(line['id'], {})
                reconcile_date = rec_info.get('max_date')
                paid_after_cutoff = float(rec_info.get('paid_after', 0.0) or 0.0)
                paid_before_cutoff = float(rec_info.get('paid_before', 0.0) or 0.0)

                current_residual = abs(line.get('amount_residual', 0.0) or 0.0)
                amount_residual_historical = current_residual
                estado_historico = ''
                if cutoff_date:
                    # Reconstruir saldo al corte: residual actual + lo que se pagó DESPUÉS del corte
                    amount_residual_historical = current_residual + paid_after_cutoff
                    # Forzar cero cuando está completamente conciliado antes/en el corte
                    if reconcile_date and reconcile_date <= cutoff_date and amount_residual_historical <= 0:
                        amount_residual_historical = 0.0

                    estado_historico = 'PAGADA' if amount_residual_historical <= 0 else 'NO PAGADA'

                    # Regla de Corte Histórico explícita:
                    #   fecha_emision <= fecha_corte  AND
                    #   (fecha_pago IS NULL  OR  fecha_pago > fecha_corte)
                    fecha_emision_linea = line.get('date') or move.get('invoice_date') or ''
                    if not self._aplica_corte_historico(
                        fecha_emision=fecha_emision_linea,
                        fecha_pago=reconcile_date,
                        amount_residual_historical=amount_residual_historical,
                        cutoff_date=cutoff_date,
                        include_reconciled=include_reconciled,
                    ):
                        continue
                
                row = {
                    'payment_state': move.get('payment_state', ''),
                    'move_id/payment_state': move.get('payment_state', ''),
                    'payment_state_display': PAYMENT_STATE_LABELS_ES.get(
                        move.get('payment_state', ''), move.get('payment_state', '')
                    ),
                    'parent_state': line.get('parent_state', ''),
                    'move_id/parent_state': line.get('parent_state', ''),
                    'move_id/state': DOCUMENT_STATE_LABELS_ES.get(move.get('state'), move.get('state') or ''),
                    'state': DOCUMENT_STATE_LABELS_ES.get(move.get('state'), move.get('state') or ''),
                    'invoice_date': move.get('invoice_date', ''),
                    'move_id/invoice_date': move.get('invoice_date', ''),
                    'account.move/invoice_date': move.get('date', ''),
                    'l10n_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'account.move/l10n_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
                    'move_name': move.get('name', ''),
                    'account.move/name': move.get('name', ''),
                    'l10n_latam_boe_number': move.get('l10n_latam_boe_number', ''),
                    'account.move/l10n_latam_boe_number': move.get('l10n_latam_boe_number', ''),
                    'invoice_origin': move.get('invoice_origin', '') or source_move.get('invoice_origin', ''),
                    'account.move/invoice_origin': move.get('invoice_origin', '') or source_move.get('invoice_origin', ''),
                    'account_id/code': account.get('code', ''),
                    'account_id/name': account.get('name', ''),
                    'partner_vat': partner.get('vat', ''),
                    'partner_name': partner.get('name', ''),
                    'partner_id': partner.get('name', ''),
                    'partner_id/vat': partner.get('vat', ''),
                    'patner_id/vat': partner.get('vat', ''),
                    'patner_id': partner.get('name', ''),
                    'partner_state': m2o_name(partner.get('state_id')),
                    'partner_district': partner.get('l10n_pe_district', ''),
                    'partner_country_code': country_code,
                    'partner_country_name': m2o_name(partner.get('country_id')),
                    'partner_id/state_id': m2o_name(partner.get('state_id')),
                    'partner_id/l10n_pe_district': partner.get('l10n_pe_district', ''),
                    'partner_id/country_code': country_code,
                    'partner_id/country_id': m2o_name(partner.get('country_id')),
                    'patner_id/state_id': m2o_name(partner.get('state_id')),
                    'patner_id/l10n_pe_district': partner.get('l10n_pe_district', ''),
                    'patner_id/country_code': country_code,
                    'patner_id/country_id': m2o_name(partner.get('country_id')),
                    'currency_id': m2o_name(account.get('currency_id') or line.get('currency_id') or move.get('currency_id')),
                    'account_id/currency_id': m2o_name(account.get('currency_id') or line.get('currency_id') or move.get('currency_id')),
                    'amount_total': move.get('amount_total', 0.0),
                    'account.move/amount_total': move.get('amount_total', 0.0),
                    'amount_residual_with_retention': move.get('amount_residual_with_retention', move.get('amount_residual', 0.0)),
                    'amount_residual_signed': move.get('amount_residual_signed', 0.0),
                    'account.move/amount_residual': move.get('amount_residual', 0.0),
                    'amount_currency': line.get('amount_currency', 0.0),
                    'amount_residual_currency': line.get('amount_residual', 0.0),
                    'amount_residual_historical': amount_residual_historical,
                    'paid_after_cutoff': paid_after_cutoff,
                    'paid_before_cutoff': paid_before_cutoff,
                    'debit': line.get('debit', 0.0) or 0.0,
                    'credit': line.get('credit', 0.0) or 0.0,
                    'balance': line.get('balance', 0.0) or 0.0,
                    'date': line.get('date', ''),
                    'date_maturity': date_maturity,
                    'invoice_date_due': move.get('invoice_date_due', ''),
                    'account.move/invoice_date_due': move.get('invoice_date_due', ''),
                    'ref': move.get('ref', ''),
                    'invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')) or m2o_name(source_move.get('invoice_payment_term_id')),
                    'account.move/invoice_payment_term_id': m2o_name(move.get('invoice_payment_term_id')) or m2o_name(source_move.get('invoice_payment_term_id')),
                    'name': line.get('name', ''),
                    'account.move.line/name': line.get('name', ''),
                    'invoice_user_name': m2o_name(move.get('invoice_user_id')) or m2o_name(source_move.get('invoice_user_id')),
                    'team_name': m2o_name(move.get('team_id')) or m2o_name(source_move.get('team_id')),
                    'account.move/invoice_user_id': m2o_name(move.get('invoice_user_id')) or m2o_name(source_move.get('invoice_user_id')),

                    # Canal de venta (misma prioridad que en get_report_lines)
                    'sales_channel_name': (
                        m2o_name(move.get('sales_channel_id'))
                        or m2o_name(source_move.get('sales_channel_id'))
                        or m2o_name(move.get('bill_form_invoices_order_channel_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_channel_id'))
                    ),
                    'account.move/sales_channel_id': (
                        m2o_name(move.get('sales_channel_id'))
                        or m2o_name(source_move.get('sales_channel_id'))
                        or m2o_name(move.get('bill_form_invoices_order_channel_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_channel_id'))
                    ),

                    # Tipo de venta (misma prioridad que en get_report_lines)
                    'sales_type_name': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),
                    'account.move/sales_type_id': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),
                    'account.move/sale_type_id': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),

                    # Línea comercial (lógica original restaurada)
                    'linea_comercial': (
                        m2o_name(move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(move.get('team_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(source_move.get('team_id'))
                    ),
                    'account.move/linea_comercial': (
                        m2o_name(move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(move.get('team_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_line_commercial_zone_id'))
                        or m2o_name(source_move.get('team_id'))
                    ),

                    'move_id/invoice_user_id': m2o_name(move.get('invoice_user_id')) or m2o_name(source_move.get('invoice_user_id')),
                    'move_id/sales_channel_id': (
                        m2o_name(move.get('sales_channel_id'))
                        or m2o_name(source_move.get('sales_channel_id'))
                        or m2o_name(move.get('bill_form_invoices_order_channel_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_channel_id'))
                    ),
                    'move_id/sales_type_id': (
                        m2o_name(move.get('sale_type_id'))
                        or m2o_name(source_move.get('sale_type_id'))
                        or m2o_name(move.get('bill_form_invoices_order_sales_type_id'))
                        or m2o_name(source_move.get('bill_form_invoices_order_sales_type_id'))
                    ),
                    'move_id/payment_state': move.get('payment_state', ''),
                    'team_id': m2o_name(move.get('team_id')) or m2o_name(source_move.get('team_id')),
                    'partner_groups': partner_groups_display,
                    'grupo_comercial': partner_groups_display,
                    'agr.credit.customer/patner_groups_ids': partner_groups_display,
                    'agr.credit.customer/partner_groups_ids': partner_groups_display,
                    'sub_channel_id': sub_channel_final,
                    'agr.credit.customer/sub_channel_id': sub_channel_final,
                    'payment_method': payment_method_display,
                    'move_id/order_id/tag_ids': payment_method_display,
                    'dias_vencido': dias_vencido,
                    'estado_deuda': estado_deuda,
                    'estado_historico': estado_historico,
                    'antiguedad': antiguedad,
                    'reconciliation_date': reconcile_date,
                }

                rows.append(row)

            # 5. Calcular metadatos de paginación
            total_pages = (total_count + per_page - 1) // per_page
            has_more = page < total_pages
            
            return {
                'data': rows,
                'total_count': total_count,
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'has_more': has_more
            }
            
        except Exception as e:
            print(f"[ERROR] Error en paginación: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def get_report_summary(self, **kwargs):
        """
        Obtiene resumen agregado directamente de Odoo usando read_group.
        Mucho más rápido que descargar todas las líneas.
        
        Args:
            **kwargs: Filtros (start_date, end_date, customer, account_codes, sales_channel_id, doc_type_id)
            
        Returns:
            dict: Resumen por cuenta y total general
        """
        try:
            print("[INFO] Obteniendo resumen de reporte CxC via read_group...")
            
            if not self.repository.is_connected():
                return None
                
            # Extraer filtros
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            customer = kwargs.get('customer')
            account_codes = kwargs.get('account_codes')
            sales_channel_id = kwargs.get('sales_channel_id')
            doc_type_id = kwargs.get('doc_type_id')
            sub_channel = kwargs.get('sub_channel')
            cutoff_date = kwargs.get('cutoff_date')
            include_reconciled = kwargs.get('include_reconciled', False)

            if cutoff_date or sub_channel:
                # Si hay fecha de corte, read_group no es suficiente para calcular paid_after_cutoff
                # Si hay sub canal, el filtro se calcula en post-proceso y tampoco aplica a read_group
                # Retornamos None para indicar que debe usarse el método tradicional
                return None

            line_domain = self._build_report_domain(
                start_date=start_date,
                end_date=end_date,
                customer=customer,
                account_codes=account_codes,
                sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id,
                sub_channel=sub_channel,
                include_reconciled=include_reconciled
            )
            
            # Campos a agregar
            fields = ['debit', 'credit', 'amount_residual', 'balance']
            groupby = ['account_id']
            
            groups = self.repository.read_group('account.move.line', line_domain, fields, groupby)
            
            overall = {
                'debit': 0.0,
                'credit': 0.0,
                'pending_cutoff': 0.0,
                'paid_after_cutoff': 0.0,
                'saldo_total': 0.0,
                'saldo': 0.0,
                'count': 0
            }
            
            by_account = []
            for g in groups:
                acc_info = g.get('account_id')
                acc_code = ''
                acc_name = ''
                if isinstance(acc_info, list) and len(acc_info) >= 2:
                    # En read_group, Odoo a veces no devuelve el código en el nombre
                    # Necesitamos el código exacto
                    acc_id = acc_info[0]
                    acc_name_full = acc_info[1]
                    # Intentar extraer código del nombre "CODE NAME"
                    parts = acc_name_full.split(' ', 1)
                    acc_code = parts[0]
                    acc_name = parts[1] if len(parts) > 1 else acc_name_full
                
                debit = float(g.get('debit', 0.0) or 0.0)
                credit = float(g.get('credit', 0.0) or 0.0)
                residual = abs(float(g.get('amount_residual', 0.0) or 0.0))
                balance = float(g.get('balance', 0.0) or 0.0)
                count = int(g.get('__count', 0))
                
                overall['debit'] += debit
                overall['credit'] += credit
                overall['pending_cutoff'] += residual
                overall['saldo_total'] += balance
                overall['count'] += count
                
                by_account.append({
                    'account_code': acc_code,
                    'account_name': acc_name,
                    'debit': debit,
                    'credit': credit,
                    'pending_cutoff': residual,
                    'paid_after_cutoff': 0.0,
                    'saldo_total': balance,
                    'saldo': balance,
                    'count': count
                })
            
            overall['saldo'] = overall['saldo_total']
            by_account.sort(key=lambda x: x['account_code'])
            
            return {
                'overall': overall,
                'by_account': by_account
            }
            
        except Exception as e:
            print(f"[ERROR] Error en get_report_summary: {e}")
            return None

    def _get_reconciliation_amounts(self, lines, cutoff_date=None):
        """
        Obtiene montos conciliados por línea y separa pagos antes/después del corte.
        Retorna dict:
        {
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
        partial_map = {p['id']: p for p in partials_data}
        
        line_map = {}
        for line_id, partials in line_to_reconcile_map.items():
            max_date = None
            paid_before = 0.0
            paid_after = 0.0
            for pid in partials:
                pdata = partial_map.get(pid)
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
                    paid_before += amount
            line_map[line_id] = {
                'max_date': max_date,
                'paid_before': paid_before,
                'paid_after': paid_after
            }
        
        return line_map
    
    # KPI Method - Disabled as per user request due to data inconsistency
    # def get_aggregated_stats(self, **kwargs):
    #     """
    #     Obtiene estadísticas agregadas usando el método get_report_lines existente.
    #     VERSIÓN CORREGIDA - Usa el método que ya funciona correctamente y tiene todos los campos calculados.
    #     
    #     Args:
    #         **kwargs: Filtros (start_date, end_date, customer, account_codes, sales_channel_id, doc_type_id)
    #     
    #     Returns:
    #         dict: {
    #             'total_count': 1234,
    #             'total_amount': 500000.00,
    #             'pending_amount': 250000.00,
    #             'overdue_amount': 50000.00,
    #             'paid_amount': 250000.00
    #         }
    #     """
    #     try:
    #         print("[INFO] Calculando estadísticas agregadas...")
    #         
    #         if not self.repository.is_connected():
    #             raise ValueError("No hay conexión a Odoo disponible")
    #         
    #         # Extraer filtros
    #         start_date = kwargs.get('start_date')
    #         end_date = kwargs.get('end_date')
    #         customer = kwargs.get('customer')
    #         account_codes = kwargs.get('account_codes')
    #         sales_channel_id = kwargs.get('sales_channel_id')
    #         doc_type_id = kwargs.get('doc_type_id')
    #         
    #         # ✅ USAR EL MÉTODO QUE YA FUNCIONA (get_report_lines)
    #         # Este método ya procesa todas las líneas y calcula dias_vencido, etc.
    #         # Limitamos a 50000 para evitar timeout, pero es suficiente para stats
    #         all_lines = self.get_report_lines(
    #             start_date=start_date,
    #             end_date=end_date,
    #             customer=customer,
    #             account_codes=account_codes,
    #             sales_channel_id=sales_channel_id,
    #             doc_type_id=doc_type_id,
    #             limit=50000  # Límite razonable para stats (antes era 10000)
    #         )
    #         
    #         if not all_lines:
    #             print("[INFO] No se encontraron líneas para calcular stats")
    #             return {
    #                 'total_count': 0,
    #                 'total_amount': 0.0,
    #                 'pending_amount': 0.0,
    #                 'overdue_amount': 0.0,
    #                 'paid_amount': 0.0
    #             }
    #         
    #         # Calcular agregados desde las líneas procesadas
    #         # Usamos los campos de la LÍNEA para evitar duplicar montos de facturas con múltiples cuotas
    #         total_count = len(all_lines)
    #         
    #         # amount_residual es en moneda compañía (Soles). Usamos abs() porque puede ser negativo (crédito)
    #         # debit/credit también en moneda compañía. Balance = debit - credit.
    #         
    #         total_amount = sum(
    #             abs(float(line.get('debit', 0) or 0) - float(line.get('credit', 0) or 0))
    #             for line in all_lines
    #         )
    #         
    #         pending_amount = sum(
    #             abs(float(line.get('amount_residual', 0) or 0))
    #             for line in all_lines
    #         )
    #         
    #         # Calcular deuda vencida usando dias_vencido que ya está calculado en get_report_lines
    #         overdue_amount = sum(
    #             abs(float(line.get('amount_residual', 0) or 0))
    #             for line in all_lines 
    #             if line.get('dias_vencido', 0) > 0
    #         )
    #         
    #         paid_amount = total_amount - pending_amount
    #         
    #         result = {
    #             'total_count': total_count,
    #             'total_amount': round(total_amount, 2),
    #             'pending_amount': round(pending_amount, 2),
    #             'overdue_amount': round(overdue_amount, 2),
    #             'paid_amount': round(paid_amount, 2)
    #         }
    #         
    #         print(f"[OK] Stats calculados: {result['total_count']} registros, Total: {result['total_amount']:,.2f}, Pendiente: {result['pending_amount']:,.2f}, Vencido: {result['overdue_amount']:,.2f}")
    #         return result
    #         
    #     except Exception as e:
    #         print(f"[ERROR] Error obteniendo stats: {e}")
    #         import traceback
    #         traceback.print_exc()
    #         return {
    #             'total_count': 0,
    #             'total_amount': 0.0,
    #             'pending_amount': 0.0,
    #             'overdue_amount': 0.0,
    #             'paid_amount': 0.0
    #         }

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
            
            # Obtener datos relacionados (en lotes)
            move_map = {}
            partner_map = {}

            if move_ids:
                move_fields = [
                    'id', 'name', 'payment_state', 'invoice_date', 'invoice_date_due',
                    'invoice_origin', 'l10n_latam_document_type_id', 'amount_total',
                    'amount_residual', 'currency_id', 'invoice_payment_term_id',
                    'invoice_user_id', 'amount_total_signed', 'amount_residual_with_retention',
                    'team_id',
                ]
                moves = self._read_in_batches('account.move', move_ids, move_fields, batch_size=300)
                move_map = {m['id']: m for m in moves}
                if payment_state:
                    move_map = {k: v for k, v in move_map.items() if v.get('payment_state') == payment_state}

            if partner_ids:
                partner_fields = ['id', 'name', 'vat', 'country_code', 'country_id']
                partners = self._read_in_batches('res.partner', partner_ids, partner_fields, batch_size=300)
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
                    'l10n_latam_document_type_id': m2o_name(move.get('l10n_latam_document_type_id')),
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
                    'team_id': m2o_name(move.get('team_id')),
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

