# -*- coding: utf-8 -*-
"""
Proveedor de datos de Cobranzas leyendo de Supabase (Fase 3, piloto).

Reproduce la interfaz pública de CollectionsService (get_report_lines,
get_filter_options, get_report_summary) consultando las tablas que puebla
scripts/etl/etl_sync_threading.py (fact_move_lines, fact_moves,
fact_partial_reconciles, dim_*) en vez de llamar a Odoo en cada request. Ver
scripts/etl/supabase_schema_collections.sql para el esquema exacto.

Decisión de implementación: se usa psycopg2 (SUPABASE_DB_URI) con SQL
parametrizado directo, en vez del cliente supabase-py/PostgREST. Los filtros de
CollectionsService._build_report_domain (prefijos de cuenta con OR, ILIKE,
rangos de fecha, corte histórico) y los joins a dim_partners/dim_accounts/
dim_sales_channels/dim_doc_types/dim_credit_customers/dim_sale_orders se
expresan de forma más simple y legible en SQL directo que como query builder
de PostgREST, y evita N llamadas HTTP para lo que aquí es una sola consulta.

Para no duplicar reglas de negocio ya validadas, se REUTILIZAN sin modificar
(solo se importan) los métodos estáticos y diccionarios de etiquetas de
CollectionsService: _parse_account_codes, _collapse_1212_lines,
_aplica_corte_historico, DOCUMENT_STATE_LABELS_ES, PAYMENT_STATE_LABELS_ES.

Limitación conocida (ver resumen final de la Fase 3): la trazabilidad
factura-origen para letras (cuenta 123, CollectionsService._build_trace_invoice_map
vía bill_form_id -> account.bill.form -> invoice_ids, con fallback por
l10n_latam_boe_number) NO se reproduce aquí. Para cuentas 122/1212/1312/132/13
el resultado es idéntico a Odoo en vivo porque esa trazabilidad solo se aplica
a cuentas que empiezan con '123'; para cuenta 123 los campos que en Odoo caían
al invoice de origen (invoice_origin, invoice_payment_term_id, invoice_user_name,
sales_channel_name, sales_type_name, linea_comercial) muestran en su lugar los
valores propios de la letra (pueden venir vacíos si Odoo los deja sin
completar directamente en el account.move de la letra).
"""

from datetime import datetime

import psycopg2
import psycopg2.extras

from app.collections.services import (
    CollectionsService,
    DOCUMENT_STATE_LABELS_ES,
    PAYMENT_STATE_LABELS_ES,
)
from app.core.calculators import calcular_dias_vencido, clasificar_antiguedad

# Mismos fragmentos de nombre permitidos que CollectionsService.get_filter_options
# usa para filtrar l10n_latam.document.type.
_ALLOWED_DOC_TYPE_FRAGMENTS = ['boleta', 'factura', 'nota de crédito', 'nota de débito']

_MAIN_SELECT_SQL = """
    SELECT
        fml.id AS line_id,
        fml.move_id,
        fml.partner_id,
        fml.account_id,
        fml.name AS line_name,
        fml.date AS line_date,
        fml.date_maturity,
        fml.amount_currency,
        fml.amount_residual AS line_amount_residual,
        fml.currency_name AS line_currency_name,
        fml.debit,
        fml.credit,
        fml.balance,
        fml.parent_state,
        fml.matched_debit_ids,
        fml.matched_credit_ids,

        fm.name AS move_name,
        fm.state AS move_state,
        fm.payment_state,
        fm.invoice_date,
        fm.date AS move_date,
        fm.invoice_date_due,
        fm.ref AS move_ref,
        fm.invoice_origin,
        fm.l10n_latam_boe_number,
        fm.amount_total,
        fm.amount_residual AS move_amount_residual,
        fm.amount_residual_with_retention,
        fm.amount_residual_signed,
        fm.currency_name AS move_currency_name,
        fm.sale_type_name,
        fm.team_id AS move_team_id,
        fm.team_name,
        fm.order_id,
        fm.invoice_payment_term_name,
        fm.invoice_user_name,
        fm.commercial_zone_name,

        dp.name AS partner_name,
        dp.vat AS partner_vat,
        dp.state_name AS partner_state_name,
        dp.country_code AS partner_country_code,
        dp.country_name AS partner_country_name,
        dp.l10n_pe_district AS partner_district,

        da.code AS account_code,
        da.name AS account_name,
        da.currency_name AS account_currency_name,

        sc.name AS sales_channel_name,
        dt.name AS doc_type_name,

        dcc.partner_groups_display,

        dso.sub_channel_name AS order_sub_channel_name,
        dso.tag_ids AS order_tag_ids

    FROM fact_move_lines fml
    LEFT JOIN fact_moves fm ON fm.id = fml.move_id
    LEFT JOIN dim_partners dp ON dp.id = fml.partner_id
    LEFT JOIN dim_accounts da ON da.id = fml.account_id
    LEFT JOIN dim_sales_channels sc ON sc.id = fm.sales_channel_id
    LEFT JOIN dim_doc_types dt ON dt.id = fm.l10n_latam_document_type_id
    LEFT JOIN dim_credit_customers dcc ON dcc.partner_id = fml.partner_id
    LEFT JOIN dim_sale_orders dso ON dso.id = fm.order_id
    WHERE {where_sql}
    ORDER BY fml.date DESC NULLS LAST, fml.id DESC
    {limit_sql}
"""


class CollectionsSupabaseProvider:
    """
    Reemplazo de CollectionsService que lee de Supabase en vez de Odoo.
    Ver docstring del módulo para el detalle de qué se reutiliza de
    CollectionsService y qué limitación conocida existe (letras/cuenta 123).
    """

    def __init__(self, db_uri):
        if not db_uri:
            raise ValueError(
                "Falta SUPABASE_DB_URI en la configuración para usar COLLECTIONS_SOURCE=supabase"
            )
        self.db_uri = db_uri

    def _connect(self):
        return psycopg2.connect(self.db_uri, cursor_factory=psycopg2.extras.RealDictCursor)

    @staticmethod
    def _d(value):
        """Normaliza una fecha (date/datetime/str/None) a 'YYYY-MM-DD' o ''."""
        if value in (None, ''):
            return ''
        if hasattr(value, 'isoformat'):
            return value.isoformat()[:10]
        return str(value)[:10]

    def _build_where(self, *, start_date, end_date, customer, account_codes, sales_channel_id,
                      doc_type_id, sub_channel, date_cutoff_start, cutoff_date,
                      include_reconciled, doc_number):
        """Traduce CollectionsService._build_report_domain a SQL. `sub_channel` no
        se puede expresar en SQL (depende de sale.order + fallback por país,
        calculado en Python), se filtra en `get_report_lines` después de traer
        las filas."""
        account_code_list = CollectionsService._parse_account_codes(account_codes)
        clauses = []
        params = {}

        if account_code_list:
            code_clauses = []
            for i, code in enumerate(account_code_list):
                key = f'acc_code_{i}'
                code_clauses.append(f"da.code LIKE %({key})s")
                params[key] = f"{code}%"
            clauses.append('(' + ' OR '.join(code_clauses) + ')')

        # Exclusión permanente de la cuenta de saldos iniciales (igual en ambas ramas).
        clauses.append("COALESCE(da.code, '') != '1239001'")

        # Dominio base de CollectionsService._build_report_domain (parent_state permitidos).
        clauses.append(
            "COALESCE(fml.parent_state, '') IN ("
            "'posted', 'portfolio', 'accepted', 'collection', "
            "'discount', 'warranty', 'disbursed', 'protested'"
            ")"
        )

        if cutoff_date:
            clauses.append("fml.date <= %(cutoff_date)s")
            params['cutoff_date'] = cutoff_date
            if date_cutoff_start and str(date_cutoff_start).strip():
                clauses.append("fml.date >= %(date_cutoff_start)s")
                params['date_cutoff_start'] = str(date_cutoff_start).strip()
        else:
            clauses.append("fml.amount_residual != 0")
            if start_date:
                clauses.append("fml.date >= %(start_date)s")
                params['start_date'] = start_date
            if end_date:
                clauses.append("fml.date <= %(end_date)s")
                params['end_date'] = end_date
            if not include_reconciled:
                clauses.append("COALESCE(fml.reconciled, FALSE) = FALSE")

        if customer:
            clauses.append("dp.name ILIKE %(customer)s")
            params['customer'] = f"%{customer}%"

        if sales_channel_id:
            clauses.append("fm.sales_channel_id = %(sales_channel_id)s")
            params['sales_channel_id'] = sales_channel_id
            if doc_type_id:
                clauses.append("fm.l10n_latam_document_type_id = %(doc_type_id)s")
                params['doc_type_id'] = doc_type_id
        elif doc_type_id:
            clauses.append("fm.l10n_latam_document_type_id = %(doc_type_id)s")
            params['doc_type_id'] = doc_type_id

        if doc_number and str(doc_number).strip():
            clauses.append("(fm.name ILIKE %(doc_number)s OR fm.l10n_latam_boe_number ILIKE %(doc_number)s)")
            params['doc_number'] = f"%{str(doc_number).strip()}%"

        return ' AND '.join(clauses) if clauses else 'TRUE', params

    def _get_reconciliation_map(self, cur, rows, cutoff_date):
        """Equivalente a CollectionsService._get_reconciliation_amounts, pero
        leyendo fact_partial_reconciles en vez de account.partial.reconcile."""
        reconcile_ids = set()
        line_to_reconcile = {}
        for r in rows:
            partials = list(r.get('matched_debit_ids') or []) + list(r.get('matched_credit_ids') or [])
            if partials:
                reconcile_ids.update(partials)
                line_to_reconcile[r['line_id']] = partials

        if not reconcile_ids:
            return {}

        cur.execute(
            "SELECT id, amount, max_date FROM fact_partial_reconciles WHERE id = ANY(%(ids)s)",
            {'ids': list(reconcile_ids)}
        )
        partial_map = {row['id']: row for row in cur.fetchall()}

        line_map = {}
        for line_id, partials in line_to_reconcile.items():
            max_date = None
            paid_before = 0.0
            paid_after = 0.0
            for pid in partials:
                pdata = partial_map.get(pid)
                if not pdata:
                    continue
                pdate = self._d(pdata.get('max_date'))
                amount = float(pdata.get('amount') or 0.0)
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
            line_map[line_id] = {'max_date': max_date, 'paid_before': paid_before, 'paid_after': paid_after}

        return line_map

    def get_report_lines(self, start_date=None, end_date=None, customer=None, limit=0,
                          account_codes=None, sales_channel_id=None, doc_type_id=None,
                          sub_channel=None, date_cutoff_start=None, payment_method=None,
                          cutoff_date=None, include_reconciled=False, doc_number=None):
        """Misma firma e igual contrato de salida que CollectionsService.get_report_lines."""
        try:
            where_sql, params = self._build_where(
                start_date=start_date, end_date=end_date, customer=customer,
                account_codes=account_codes, sales_channel_id=sales_channel_id,
                doc_type_id=doc_type_id, sub_channel=sub_channel,
                date_cutoff_start=date_cutoff_start, cutoff_date=cutoff_date,
                include_reconciled=include_reconciled, doc_number=doc_number,
            )
            limit_sql = ''
            effective_limit = limit if limit and limit > 0 else None
            if effective_limit:
                params['row_limit'] = effective_limit
                limit_sql = 'LIMIT %(row_limit)s'

            sql = _MAIN_SELECT_SQL.format(where_sql=where_sql, limit_sql=limit_sql)

            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    raw_rows = cur.fetchall()

                    if not raw_rows:
                        return []

                    reconciliation_map = {}
                    if cutoff_date:
                        reconciliation_map = self._get_reconciliation_map(cur, raw_rows, cutoff_date)

                    cur.execute("SELECT id, name FROM dim_payment_tags")
                    tag_name_map = {row['id']: row.get('name') or '' for row in cur.fetchall()}
            finally:
                conn.close()

            today = datetime.today().date()
            rows = []
            for r in raw_rows:
                row = self._build_row(
                    r, cutoff_date=cutoff_date, include_reconciled=include_reconciled,
                    reconciliation_map=reconciliation_map, tag_name_map=tag_name_map, today=today,
                )
                if row is None:
                    continue  # excluida por la regla de corte histórico

                # Filtros de post-proceso (igual que CollectionsService.get_report_lines):
                # sub_channel y payment_method dependen de datos ya calculados por fila,
                # no se pueden expresar como filtro SQL simple.
                if sub_channel and str(sub_channel).strip():
                    if row['sub_channel_id'].strip().upper() != str(sub_channel).strip().upper():
                        continue
                if payment_method and str(payment_method).strip():
                    try:
                        pm_id = int(payment_method)
                        if pm_id not in (r.get('order_tag_ids') or []):
                            continue
                    except (ValueError, TypeError):
                        pass

                rows.append(row)

            rows = CollectionsService._collapse_1212_lines(rows, today)
            return rows

        except Exception as e:
            print(f"[ERROR] CollectionsSupabaseProvider.get_report_lines: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _build_row(self, r, *, cutoff_date, include_reconciled, reconciliation_map, tag_name_map, today):
        line_id = r['line_id']
        rec_info = reconciliation_map.get(line_id, {})
        reconcile_date = rec_info.get('max_date')
        paid_after_cutoff = float(rec_info.get('paid_after', 0.0) or 0.0)
        paid_before_cutoff = float(rec_info.get('paid_before', 0.0) or 0.0)

        current_residual = abs(float(r.get('line_amount_residual') or 0.0))
        amount_residual_historical = current_residual
        estado_historico = ''
        if cutoff_date:
            amount_residual_historical = current_residual + paid_after_cutoff
            if reconcile_date and reconcile_date <= cutoff_date and amount_residual_historical <= 0:
                amount_residual_historical = 0.0
            estado_historico = 'PAGADA' if amount_residual_historical <= 0 else 'NO PAGADA'

            fecha_emision_linea = self._d(r.get('line_date')) or self._d(r.get('invoice_date')) or ''
            if not CollectionsService._aplica_corte_historico(
                fecha_emision=fecha_emision_linea,
                fecha_pago=reconcile_date,
                amount_residual_historical=amount_residual_historical,
                cutoff_date=cutoff_date,
                include_reconciled=include_reconciled,
            ):
                return None

        date_maturity = self._d(r.get('date_maturity'))
        dias_vencido = calcular_dias_vencido(date_maturity, today) if date_maturity else 0
        antiguedad = clasificar_antiguedad(max(0, dias_vencido))
        estado_deuda = 'VENCIDO' if dias_vencido > 0 else 'VIGENTE'

        partner_name = r.get('partner_name') or ''
        account_code = r.get('account_code') or ''
        country_code = r.get('partner_country_code') or ''
        currency_display = r.get('account_currency_name') or r.get('line_currency_name') or r.get('move_currency_name') or ''
        linea_comercial = r.get('commercial_zone_name') or r.get('team_name') or ''
        move_state = r.get('move_state')
        payment_state = r.get('payment_state') or ''

        order_tag_ids = r.get('order_tag_ids') or []
        payment_method_display = ', '.join(tag_name_map[tid] for tid in order_tag_ids if tid in tag_name_map)

        sub_channel_raw = (r.get('order_sub_channel_name') or '') if r.get('order_id') else ''
        if not sub_channel_raw or sub_channel_raw == 'N/A' or sub_channel_raw.strip() == '':
            if country_code == 'PE':
                sub_channel_final = 'NACIONAL'
            elif country_code:
                sub_channel_final = 'INTERNACIONAL'
            else:
                sub_channel_final = 'N/A'
        else:
            sub_channel_final = sub_channel_raw

        move_amount_residual = float(r.get('move_amount_residual') or 0.0)
        amount_residual_with_retention = r.get('amount_residual_with_retention')
        amount_residual_with_retention = (
            float(amount_residual_with_retention)
            if amount_residual_with_retention is not None
            else move_amount_residual
        )

        return {
            'payment_state': payment_state,
            'move_id/payment_state': payment_state,
            'payment_state_display': PAYMENT_STATE_LABELS_ES.get(payment_state, payment_state),
            'parent_state': r.get('parent_state') or '',
            'move_id/parent_state': r.get('parent_state') or '',
            'move_id/state': DOCUMENT_STATE_LABELS_ES.get(move_state, move_state or ''),
            'state': DOCUMENT_STATE_LABELS_ES.get(move_state, move_state or ''),
            'invoice_date': self._d(r.get('invoice_date')),
            'move_id/invoice_date': self._d(r.get('invoice_date')),
            'account.move/invoice_date': self._d(r.get('move_date')),
            'l10n_latam_document_type_id': r.get('doc_type_name') or '',
            'account.move/l10n_latam_document_type_id': r.get('doc_type_name') or '',
            'move_name': r.get('move_name') or '',
            'account.move/name': r.get('move_name') or '',
            'l10n_latam_boe_number': r.get('l10n_latam_boe_number') or '',
            'account.move/l10n_latam_boe_number': r.get('l10n_latam_boe_number') or '',
            'invoice_origin': r.get('invoice_origin') or '',
            'account.move/invoice_origin': r.get('invoice_origin') or '',
            'account_id/code': account_code,
            'account_id/name': r.get('account_name') or '',
            'partner_vat': r.get('partner_vat') or '',
            'partner_name': partner_name,
            'partner_id': partner_name,
            'patner_id/vat': r.get('partner_vat') or '',
            'patner_id': partner_name,
            'partner_state': r.get('partner_state_name') or '',
            'partner_district': r.get('partner_district') or '',
            'partner_country_code': country_code,
            'partner_country_name': r.get('partner_country_name') or '',
            'patner_id/state_id': r.get('partner_state_name') or '',
            'patner_id/l10n_pe_district': r.get('partner_district') or '',
            'patner_id/country_code': country_code,
            'patner_id/country_id': r.get('partner_country_name') or '',
            'currency_id': currency_display,
            'account_id/currency_id': currency_display,
            'amount_total': float(r.get('amount_total') or 0.0),
            'account.move/amount_total': float(r.get('amount_total') or 0.0),
            'amount_residual_with_retention': amount_residual_with_retention,
            'amount_residual_signed': float(r.get('amount_residual_signed') or 0.0),
            'account.move/amount_residual': move_amount_residual,
            'amount_currency': float(r.get('amount_currency') or 0.0),
            'amount_residual_currency': float(r.get('line_amount_residual') or 0.0),
            'amount_residual_historical': amount_residual_historical,
            'paid_after_cutoff': paid_after_cutoff,
            'paid_before_cutoff': paid_before_cutoff,
            'debit': float(r.get('debit') or 0.0),
            'credit': float(r.get('credit') or 0.0),
            'balance': float(r.get('balance') or 0.0),
            'date': self._d(r.get('line_date')),
            'date_maturity': date_maturity,
            'invoice_date_due': self._d(r.get('invoice_date_due')),
            'account.move/invoice_date_due': self._d(r.get('invoice_date_due')),
            'ref': r.get('move_ref') or '',
            'invoice_payment_term_id': r.get('invoice_payment_term_name') or '',
            'account.move/invoice_payment_term_id': r.get('invoice_payment_term_name') or '',
            'name': r.get('line_name') or '',
            'account.move.line/name': r.get('line_name') or '',
            'invoice_user_name': r.get('invoice_user_name') or '',
            'account.move/invoice_user_id': r.get('invoice_user_name') or '',
            'sales_channel_name': r.get('sales_channel_name') or '',
            'account.move/sales_channel_id': r.get('sales_channel_name') or '',
            'sales_type_name': r.get('sale_type_name') or '',
            'account.move/sales_type_id': r.get('sale_type_name') or '',
            'account.move/sale_type_id': r.get('sale_type_name') or '',
            'linea_comercial': linea_comercial,
            'account.move/linea_comercial': linea_comercial,
            'team_name': r.get('team_name') or '',
            'move_id/invoice_user_id': r.get('invoice_user_name') or '',
            'move_id/sales_channel_id': r.get('sales_channel_name') or '',
            'move_id/sales_type_id': r.get('sale_type_name') or '',
            'move_id/payment_state': payment_state,
            'team_id': r.get('team_name') or '',
            'partner_groups': r.get('partner_groups_display') or '',
            'grupo_comercial': r.get('partner_groups_display') or '',
            'agr.credit.customer/patner_groups_ids': r.get('partner_groups_display') or '',
            'agr.credit.customer/partner_groups_ids': r.get('partner_groups_display') or '',
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

    def get_report_summary(self, **kwargs):
        """
        A diferencia de CollectionsService.get_report_summary (que usa
        read_group nativo de Odoo), aquí se devuelve None siempre: el llamador
        (app/collections/routes.py::report_account12) interpreta None como
        'usar el camino completo vía get_report_lines + _summarize', que sigue
        siendo rápido contra Postgres local (a diferencia de Odoo XML-RPC).
        Ver limitación conocida en el resumen final de la Fase 3.
        """
        return None

    def get_filter_options(self, start_date=None, end_date=None, customer=None,
                            account_codes=None, sales_channel_id=None, cutoff_date=None,
                            include_reconciled=False):
        try:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, name FROM dim_sales_channels ORDER BY name")
                    sales_channels = [{'id': row['id'], 'name': row['name'] or ''} for row in cur.fetchall()]

                    cur.execute(
                        "SELECT DISTINCT sub_channel_name FROM dim_credit_customers "
                        "WHERE sub_channel_name IS NOT NULL AND sub_channel_name != ''"
                    )
                    sub_channel_set = {'NACIONAL', 'INTERNACIONAL'}
                    sub_channel_set.update(row['sub_channel_name'] for row in cur.fetchall())
                    sub_channels = [{'value': name, 'name': name} for name in sorted(sub_channel_set)]

                    cur.execute("SELECT id, name FROM dim_doc_types ORDER BY name")
                    all_doc_types = cur.fetchall()

                    document_types = []
                    for doc in all_doc_types:
                        doc_name = doc.get('name') or ''
                        if not any(frag in doc_name.lower() for frag in _ALLOWED_DOC_TYPE_FRAGMENTS):
                            continue
                        where_sql, params = self._build_where(
                            start_date=start_date, end_date=end_date, customer=customer,
                            account_codes=account_codes, sales_channel_id=sales_channel_id,
                            doc_type_id=doc['id'], sub_channel=None, date_cutoff_start=None,
                            cutoff_date=cutoff_date, include_reconciled=include_reconciled,
                            doc_number=None,
                        )
                        count_sql = (
                            "SELECT COUNT(*) AS n FROM fact_move_lines fml "
                            "LEFT JOIN fact_moves fm ON fm.id = fml.move_id "
                            "LEFT JOIN dim_partners dp ON dp.id = fml.partner_id "
                            "LEFT JOIN dim_accounts da ON da.id = fml.account_id "
                            f"WHERE {where_sql}"
                        )
                        cur.execute(count_sql, params)
                        doc_count = cur.fetchone()['n']
                        if doc_count > 0:
                            document_types.append({'id': doc['id'], 'name': doc_name})

                    cur.execute("SELECT id, name FROM dim_payment_tags ORDER BY name")
                    payment_methods = [{'id': row['id'], 'name': row['name'] or ''} for row in cur.fetchall()]
            finally:
                conn.close()

            return {
                'sales_channels': sales_channels,
                'document_types': document_types,
                'sub_channels': sub_channels,
                'payment_methods': payment_methods,
            }
        except Exception as e:
            print(f"[ERROR] CollectionsSupabaseProvider.get_filter_options: {e}")
            import traceback
            traceback.print_exc()
            return {'sales_channels': [], 'document_types': [], 'sub_channels': [], 'payment_methods': []}

    @staticmethod
    def filter_nacional(rows):
        """Delegado directo: es un filtro puro sobre filas ya obtenidas, no depende
        de la fuente de datos."""
        return CollectionsService.filter_nacional(rows)

    @staticmethod
    def filter_internacional(rows):
        return CollectionsService.filter_internacional(rows)
