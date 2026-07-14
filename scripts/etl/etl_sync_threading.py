# -*- coding: utf-8 -*-
"""
Script ETL (Extract, Transform, Load) para sincronizar Odoo -> Supabase.
Maneja Facturas, Notas de Crédito, Letras y (Fase 3) el piloto de Cobranzas:
líneas de asiento (fact_move_lines), conciliaciones (fact_partial_reconciles)
y dimensiones (cuentas, canales de venta, tipos de documento, clientes de
crédito, órdenes de venta) que consume app/collections/supabase_provider.py.

Sincronización incremental: cada modelo lleva su propia marca de agua (watermark) en la
tabla `etl_sync_state` de Supabase (ver scripts/etl/supabase_schema_etl_state.sql). Si ya
existe un último sync exitoso, solo se traen registros con `write_date` posterior; si no,
se trae el histórico completo paginando en lotes de PAGE_SIZE. Las dimensiones chicas
(cuentas, canales, tipos de documento, clientes de crédito) se sincronizan completas en
cada corrida por simplicidad, dado su volumen reducido.
"""

import os
import logging
import traceback
import xmlrpc.client
from datetime import datetime, timezone
from supabase import create_client

logger = logging.getLogger(__name__)

PAGE_SIZE = 2000

# Modelos lógicos usados como clave en etl_sync_state (no son modelos de Odoo, identifican
# cada dominio de búsqueda distinto que corremos sobre account.move).
SYNC_KEY_MOVES = 'account.move.invoices'
SYNC_KEY_LETTERS = 'account.move.letters'

# --- Piloto Cobranzas (Fase 3): claves de watermark para los dominios nuevos ---
SYNC_KEY_MOVE_LINES_COLLECTIONS = 'account.move.line.collections'
SYNC_KEY_PARTIAL_RECONCILES = 'account.partial.reconcile'
SYNC_KEY_DIM_ACCOUNTS = 'dim.accounts'
SYNC_KEY_DIM_SALES_CHANNELS = 'dim.sales_channels'
SYNC_KEY_DIM_DOC_TYPES = 'dim.doc_types'
SYNC_KEY_DIM_CREDIT_CUSTOMERS = 'dim.credit_customers'
SYNC_KEY_DIM_SALE_ORDERS = 'dim.sale_orders'

# Prefijos de cuenta contable usados por Cobranzas. Debe mantenerse igual a
# CollectionsService._parse_account_codes (app/collections/services.py) — se
# duplica aquí (en vez de importar app.collections) para que el script ETL siga
# siendo standalone y no arrastre el árbol de imports completo de Flask/la app.
COLLECTIONS_ACCOUNT_CODE_PREFIXES = ['122', '1212', '123', '1312', '132', '13']


def _load_env_if_standalone():
    """
    Carga variables de entorno desde el .env correspondiente SOLO si el script se ejecuta
    de forma standalone (`python scripts/etl/etl_sync_threading.py`).

    Cuando lo invoca la tarea Celery (app/tasks.py -> app/core/celery_utils.py), el proceso
    corre dentro del contexto de la app Flask (celery_worker.py -> create_app(...)), que ya
    cargó el .env correcto según el entorno activo (APP_ENV/FLASK_ENV/ENV). Antes este script
    forzaba siempre .env.produccion sin importar el entorno real; ahora respeta el entorno
    activo del proceso y solo actúa como fallback para ejecución manual/debug.
    """
    from dotenv import load_dotenv

    app_env = (os.getenv('APP_ENV') or os.getenv('FLASK_ENV') or os.getenv('ENV') or 'development').lower()
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    env_file = '.env.produccion' if app_env == 'production' else '.env.desarrollo'
    env_path = os.path.join(base_dir, env_file)

    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info("[INIT] Ejecución standalone: configuración cargada desde %s", env_path)
    else:
        logger.warning("[INIT] Ejecución standalone: no se encontró %s, se usan solo variables ya presentes en el entorno", env_path)


def _get_env_clean(key):
    """Limpia comillas accidentales en variables de entorno."""
    val = os.getenv(key)
    return val.replace('"', '').replace("'", '') if val else None


def _to_odoo_datetime(iso_timestamp):
    """
    Convierte un timestamp ISO 8601 (como el que se guarda en etl_sync_state) al formato
    'YYYY-MM-DD HH:MM:SS' (UTC naive) que espera Odoo en los dominios de búsqueda sobre
    campos datetime como write_date.
    """
    if not iso_timestamp:
        return None
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        logger.warning("No se pudo parsear last_synced_at='%s', se ignora el filtro incremental", iso_timestamp)
        return None


class OdooSync:
    def __init__(self):
        self.odoo_url = _get_env_clean('ODOO_URL')
        self.odoo_db = _get_env_clean('ODOO_DB')
        self.odoo_user = _get_env_clean('ODOO_USER')
        self.odoo_password = _get_env_clean('ODOO_PASSWORD')
        supabase_url = _get_env_clean('SUPABASE_URL')
        supabase_key = _get_env_clean('SUPABASE_KEY')

        self.common = xmlrpc.client.ServerProxy(f'{self.odoo_url}/xmlrpc/2/common')
        self.uid = self.common.authenticate(self.odoo_db, self.odoo_user, self.odoo_password, {})
        self.models = xmlrpc.client.ServerProxy(f'{self.odoo_url}/xmlrpc/2/object')
        self.supabase = create_client(supabase_url, supabase_key)
        logger.info("[INIT] Conectado a Odoo UID: %s", self.uid)

    def _execute_kw(self, model, method, args_list, kwargs=None):
        return self.models.execute_kw(
            self.odoo_db, self.uid, self.odoo_password, model, method, args_list, kwargs or {}
        )

    def _search_all_ids(self, model, domain, page_size=PAGE_SIZE):
        """
        Pagina `search` para traer TODOS los ids que cumplan el domain, sin límite fijo.
        Antes se usaba `limit: 500`, lo que truncaba el histórico; ahora itera con
        offset hasta agotar resultados.
        """
        all_ids = []
        offset = 0
        while True:
            batch = self._execute_kw(model, 'search', [domain], {'offset': offset, 'limit': page_size})
            if not batch:
                break
            all_ids.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        return all_ids

    def get_last_sync(self, model_name):
        """Lee el último timestamp de sync exitoso para `model_name` desde etl_sync_state."""
        try:
            response = (
                self.supabase.table('etl_sync_state')
                .select('last_synced_at')
                .eq('model_name', model_name)
                .limit(1)
                .execute()
            )
            rows = response.data or []
            if rows and rows[0].get('last_synced_at'):
                return rows[0]['last_synced_at']
        except Exception as e:
            logger.warning("No se pudo leer etl_sync_state para '%s': %s", model_name, e)
        return None

    def set_last_sync(self, model_name, timestamp_iso):
        """Actualiza (upsert) el timestamp de sync exitoso para `model_name`."""
        try:
            self.supabase.table('etl_sync_state').upsert({
                'model_name': model_name,
                'last_synced_at': timestamp_iso,
            }).execute()
        except Exception as e:
            logger.warning("No se pudo actualizar etl_sync_state para '%s': %s", model_name, e)

    def _clean_m2o(self, field):
        """Extrae el ID de un campo Many2One [id, 'name'] -> id"""
        if isinstance(field, list) and len(field) > 0:
            return field[0]
        return None

    def _clean_m2o_name(self, field):
        """
        Extrae el nombre para mostrar de un campo Many2One [id, 'name'] -> 'name'.
        Odoo ya devuelve el display_name junto con el id en toda lectura/search_read
        de un many2one, así que esto evita una consulta adicional por dimensión
        para campos que solo se usan para mostrar texto (ver columnas *_name en
        scripts/etl/supabase_schema_collections.sql).
        """
        if isinstance(field, list) and len(field) >= 2:
            return field[1]
        return None

    def _clean_date(self, date_str):
        """Asegura formato fecha"""
        return date_str if date_str else None

    def sync_partners(self, partner_ids):
        """Sincroniza socios específicos a dim_partners"""
        if not partner_ids:
            return

        logger.info("[PARTNERS] Sincronizando %s socios...", len(partner_ids))
        fields = [
            'id', 'name', 'vat', 'country_id', 'state_id', 'is_company', 'email', 'phone',
            'supplier_rank', 'customer_rank',
            # Necesarios para el piloto Cobranzas (sub_channel_id fallback por país/distrito,
            # ver CollectionsService.get_report_lines). `country_code` ya existía en la
            # columna de dim_partners pero antes nadie la poblaba.
            'l10n_pe_district',
        ]
        partners = self._execute_kw('res.partner', 'read', [list(partner_ids)], {'fields': fields})

        # res.partner.country_id solo trae [id, display_name]; se necesita el código ISO
        # (ej. 'PE'), que vive en res.country.code, así que se resuelve en un batch aparte.
        country_ids = {p['country_id'][0] for p in partners if p.get('country_id')}
        country_map = {}
        if country_ids:
            countries = self._execute_kw('res.country', 'read', [list(country_ids)], {'fields': ['id', 'code', 'name']})
            country_map = {c['id']: c for c in countries}

        data_to_upsert = []
        for p in partners:
            state_name = p['state_id'][1] if p.get('state_id') else None
            country_id = self._clean_m2o(p.get('country_id'))
            country = country_map.get(country_id, {})

            data_to_upsert.append({
                'id': p['id'],
                'name': p['name'],
                'vat': p['vat'],
                'state_name': state_name,
                'country_code': country.get('code'),
                'country_name': country.get('name'),
                'l10n_pe_district': p.get('l10n_pe_district') or '',
                'is_company': p.get('is_company', False),
                'email': str(p.get('email') or ''),
                'phone': str(p.get('phone') or ''),
                'supplier_rank': p.get('supplier_rank', 0),
                'customer_rank': p.get('customer_rank', 0),
                'last_updated_at': datetime.now(timezone.utc).isoformat()
            })

        if data_to_upsert:
            self.supabase.table('dim_partners').upsert(data_to_upsert).execute()
            logger.info("[PARTNERS] %s actualizados", len(data_to_upsert))

    # Campos de account.move leídos tanto por sync_moves() como por
    # sync_move_lines() (vía _upsert_move_headers_batch) para poblar fact_moves.
    # Incluye los campos ampliados del piloto Cobranzas (Fase 3), ver
    # CollectionsService.get_report_lines (app/collections/services.py).
    MOVE_HEADER_FIELDS = [
        'id', 'name', 'ref', 'date', 'invoice_date', 'invoice_date_due',
        'state', 'move_type', 'payment_state', 'currency_id',
        'amount_total', 'amount_residual', 'amount_untaxed',
        'partner_id', 'reversed_entry_id',
        'bill_form_id', 'invoice_origin', 'l10n_latam_document_type_id',
        'l10n_latam_boe_number', 'sales_channel_id', 'sale_type_id', 'team_id',
        'order_id', 'amount_residual_with_retention', 'amount_residual_signed',
        'invoice_payment_term_id', 'invoice_user_id',
        'bill_form_invoices_order_sales_line_commercial_zone_id',
    ]

    def _upsert_move_headers_batch(self, batch_ids):
        """
        Lee un lote de account.move por id (sin domain/estado: cualquier tipo o
        estado) y hace upsert de sus cabeceras en fact_moves. Se usa desde
        sync_moves() y desde sync_move_lines(): esta última necesita poder
        traer también letras (in_bill) y otros estados custom (portfolio,
        accepted, collection, etc. — ver DOCUMENT_STATE_LABELS_ES en
        app/collections/services.py) que sync_moves() no cubre porque su
        dominio se limita a facturas/NC posted/draft.
        """
        if not batch_ids:
            return
        moves = self._execute_kw('account.move', 'read', [batch_ids], {'fields': self.MOVE_HEADER_FIELDS})

        partner_ids = set()
        for m in moves:
            pid = self._clean_m2o(m.get('partner_id'))
            if pid:
                partner_ids.add(pid)
        self.sync_partners(partner_ids)

        data_to_upsert = []
        for m in moves:
            data_to_upsert.append({
                'id': m['id'],
                'name': m['name'],
                'ref': m.get('ref') or '',
                'date': self._clean_date(m.get('date')),
                'invoice_date': self._clean_date(m.get('invoice_date')),
                'invoice_date_due': self._clean_date(m.get('invoice_date_due')),
                'state': m.get('state'),
                'move_type': m.get('move_type'),
                'payment_state': m.get('payment_state'),
                'currency_id': self._clean_m2o(m.get('currency_id')),
                'currency_name': self._clean_m2o_name(m.get('currency_id')),
                'amount_total': m.get('amount_total', 0),
                'amount_residual': m.get('amount_residual', 0),
                'amount_untaxed': m.get('amount_untaxed', 0),
                'partner_id': self._clean_m2o(m.get('partner_id')),
                'reversed_entry_id': self._clean_m2o(m.get('reversed_entry_id')),
                # --- Campos ampliados Cobranzas (Fase 3) ---
                'bill_form_id': self._clean_m2o(m.get('bill_form_id')),
                'invoice_origin': m.get('invoice_origin') or '',
                'l10n_latam_document_type_id': self._clean_m2o(m.get('l10n_latam_document_type_id')),
                'l10n_latam_boe_number': m.get('l10n_latam_boe_number') or None,
                'sales_channel_id': self._clean_m2o(m.get('sales_channel_id')),
                'sale_type_id': self._clean_m2o(m.get('sale_type_id')),
                'sale_type_name': self._clean_m2o_name(m.get('sale_type_id')),
                'team_id': self._clean_m2o(m.get('team_id')),
                'team_name': self._clean_m2o_name(m.get('team_id')),
                'order_id': self._clean_m2o(m.get('order_id')),
                'amount_residual_with_retention': m.get('amount_residual_with_retention', m.get('amount_residual', 0)),
                'amount_residual_signed': m.get('amount_residual_signed', 0),
                'invoice_payment_term_id': self._clean_m2o(m.get('invoice_payment_term_id')),
                'invoice_payment_term_name': self._clean_m2o_name(m.get('invoice_payment_term_id')),
                'invoice_user_id': self._clean_m2o(m.get('invoice_user_id')),
                'invoice_user_name': self._clean_m2o_name(m.get('invoice_user_id')),
                'bill_form_invoices_order_sales_line_commercial_zone_id': self._clean_m2o(
                    m.get('bill_form_invoices_order_sales_line_commercial_zone_id')
                ),
                'commercial_zone_name': self._clean_m2o_name(
                    m.get('bill_form_invoices_order_sales_line_commercial_zone_id')
                ),
                'last_updated_at': datetime.now(timezone.utc).isoformat()
            })

        if data_to_upsert:
            self.supabase.table('fact_moves').upsert(data_to_upsert).execute()

    def sync_moves(self):
        """
        Sincroniza Facturas y Notas de Crédito (In/Out), de forma incremental cuando ya
        existe un sync previo exitoso.
        """
        logger.info("[MOVES] Iniciando sincronización de Movimientos...")
        last_sync = self.get_last_sync(SYNC_KEY_MOVES)
        last_sync_odoo = _to_odoo_datetime(last_sync)

        domain = [
            ('state', 'in', ['posted', 'draft']),
            ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'])
        ]
        if last_sync_odoo:
            domain.append(('write_date', '>=', last_sync_odoo))
            logger.info("[MOVES] Sync incremental desde write_date >= %s", last_sync_odoo)
        else:
            logger.info("[MOVES] Sin sync previo registrado: se trae el histórico completo")

        move_ids = self._search_all_ids('account.move', domain)

        if not move_ids:
            logger.info("[MOVES] No se encontraron movimientos nuevos/modificados.")
            self.set_last_sync(SYNC_KEY_MOVES, datetime.now(timezone.utc).isoformat())
            return

        sync_started_at = datetime.now(timezone.utc).isoformat()

        for offset in range(0, len(move_ids), PAGE_SIZE):
            batch_ids = move_ids[offset:offset + PAGE_SIZE]
            try:
                self._upsert_move_headers_batch(batch_ids)
                logger.info("[MOVES] %s movimientos sincronizados (offset=%s)", len(batch_ids), offset)
            except Exception as e:
                logger.error("[ERROR] Fallo al guardar moves (offset=%s): %s", offset, e)

        self.set_last_sync(SYNC_KEY_MOVES, sync_started_at)

    def sync_letters(self):
        """
        Sincroniza Letras de Cambio y sus relaciones con facturas, de forma incremental
        cuando ya existe un sync previo exitoso.
        """
        logger.info("[LETTERS] Iniciando sincronización de Letras...")
        last_sync = self.get_last_sync(SYNC_KEY_LETTERS)
        last_sync_odoo = _to_odoo_datetime(last_sync)

        domain = [('l10n_latam_boe_number', '!=', False)]
        if last_sync_odoo:
            domain.append(('write_date', '>=', last_sync_odoo))
            logger.info("[LETTERS] Sync incremental desde write_date >= %s", last_sync_odoo)
        else:
            logger.info("[LETTERS] Sin sync previo registrado: se trae el histórico completo")

        fields = [
            'id', 'name', 'l10n_latam_boe_number', 'state', 'date',
            'invoice_date_due', 'amount_total', 'partner_id', 'move_type',
            'bill_form_invoices'  # Campo CLAVE
        ]

        letter_ids = self._search_all_ids('account.move', domain)

        if not letter_ids:
            logger.info("[LETTERS] No se encontraron letras nuevas/modificadas.")
            self.set_last_sync(SYNC_KEY_LETTERS, datetime.now(timezone.utc).isoformat())
            return

        sync_started_at = datetime.now(timezone.utc).isoformat()

        for offset in range(0, len(letter_ids), PAGE_SIZE):
            batch_ids = letter_ids[offset:offset + PAGE_SIZE]
            letters = self._execute_kw('account.move', 'read', [batch_ids], {'fields': fields})

            partner_ids = set()
            for l in letters:
                pid = self._clean_m2o(l.get('partner_id'))
                if pid:
                    partner_ids.add(pid)
            self.sync_partners(partner_ids)

            letters_to_upsert = []
            relations_to_upsert = []

            for l in letters:
                letters_to_upsert.append({
                    'id': l['id'],
                    'name': l['name'],
                    'boe_number': l.get('l10n_latam_boe_number'),
                    'state': l.get('state'),
                    'date': self._clean_date(l.get('date')),
                    'due_date': self._clean_date(l.get('invoice_date_due')),
                    'amount_total': l.get('amount_total', 0),
                    'partner_id': self._clean_m2o(l.get('partner_id')),
                    'move_type': l.get('move_type'),
                    'last_updated_at': datetime.now(timezone.utc).isoformat()
                })

                invoice_ids = l.get('bill_form_invoices', [])
                for inv_id in invoice_ids:
                    relations_to_upsert.append({
                        'letter_id': l['id'],
                        'move_id': inv_id
                    })

            try:
                self.supabase.table('fact_letters').upsert(letters_to_upsert).execute()
                logger.info("[LETTERS] %s letras sincronizadas (offset=%s)", len(letters_to_upsert), offset)

                if relations_to_upsert:
                    self.supabase.table('rel_letter_moves').upsert(relations_to_upsert).execute()
                    logger.info("[RELATIONS] %s relaciones letra-factura creadas (offset=%s)", len(relations_to_upsert), offset)

            except Exception as e:
                logger.error("[ERROR] Fallo al guardar letras/relaciones (offset=%s): %s", offset, e)

        self.set_last_sync(SYNC_KEY_LETTERS, sync_started_at)

    # ------------------------------------------------------------------
    # Piloto Cobranzas (Fase 3): línea de asiento + conciliaciones + dimensiones
    # ------------------------------------------------------------------

    @staticmethod
    def _account_code_prefix_domain(field_path='account_id.code'):
        """Arma el bloque OR de prefijos de cuenta (mismo patrón que
        CollectionsService._build_report_domain) para un `field_path` dado,
        de forma que sirva tanto para account.move.line directo
        ('account_id.code') como para account.partial.reconcile a través de
        sus líneas ('debit_move_id.account_id.code' / 'credit_move_id...').
        """
        terms = [(field_path, '=like', f'{code}%') for code in COLLECTIONS_ACCOUNT_CODE_PREFIXES]
        if len(terms) == 1:
            return [terms[0]]
        return (['|'] * (len(terms) - 1)) + terms

    _MOVE_LINE_FIELDS = [
        'id', 'move_id', 'partner_id', 'account_id', 'name', 'date',
        'date_maturity', 'amount_currency', 'amount_residual', 'currency_id',
        'debit', 'credit', 'balance', 'parent_state',
        'matched_debit_ids', 'matched_credit_ids', 'reconciled',
    ]

    def sync_move_lines(self):
        """
        Sincroniza account.move.line de las cuentas 12x usadas por Cobranzas
        hacia fact_move_lines. Mismo dominio base que
        CollectionsService._build_report_domain, sin filtros de fecha/corte
        (esos se aplican en cada request desde app/collections/supabase_provider.py).
        """
        logger.info("[MOVE_LINES] Iniciando sincronización de líneas CxC (Cobranzas)...")
        last_sync = self.get_last_sync(SYNC_KEY_MOVE_LINES_COLLECTIONS)
        last_sync_odoo = _to_odoo_datetime(last_sync)

        domain = [
            ('account_id.reconcile', '=', True),
            ('parent_state', 'in', (
                'posted', 'portfolio', 'accepted', 'collection',
                'discount', 'warranty', 'disbursed', 'protested'
            )),
            ('account_id.code', '!=', '1239001'),
        ] + self._account_code_prefix_domain('account_id.code')

        if last_sync_odoo:
            domain.append(('write_date', '>=', last_sync_odoo))
            logger.info("[MOVE_LINES] Sync incremental desde write_date >= %s", last_sync_odoo)
        else:
            logger.info("[MOVE_LINES] Sin sync previo registrado: se trae el histórico completo")

        fields = self._MOVE_LINE_FIELDS

        line_ids = self._search_all_ids('account.move.line', domain)

        if not line_ids:
            logger.info("[MOVE_LINES] No se encontraron líneas nuevas/modificadas.")
            self.set_last_sync(SYNC_KEY_MOVE_LINES_COLLECTIONS, datetime.now(timezone.utc).isoformat())
            return

        sync_started_at = datetime.now(timezone.utc).isoformat()

        for offset in range(0, len(line_ids), PAGE_SIZE):
            batch_ids = line_ids[offset:offset + PAGE_SIZE]
            lines = self._execute_kw('account.move.line', 'read', [batch_ids], {'fields': fields})
            n = self._upsert_move_lines_from_odoo(lines or [])
            logger.info("[MOVE_LINES] %s líneas sincronizadas (offset=%s)", n, offset)

        self.set_last_sync(SYNC_KEY_MOVE_LINES_COLLECTIONS, sync_started_at)

    def _upsert_move_lines_from_odoo(self, lines):
        """Persiste en fact_move_lines registros ya leídos desde Odoo."""
        if not lines:
            return 0

        move_ids_in_batch = list({self._clean_m2o(l.get('move_id')) for l in lines if l.get('move_id')})
        partner_ids_in_batch = list({self._clean_m2o(l.get('partner_id')) for l in lines if l.get('partner_id')})
        try:
            if partner_ids_in_batch:
                self.sync_partners(partner_ids_in_batch)
            self._upsert_move_headers_batch(move_ids_in_batch)
        except Exception as e:
            logger.error("[ERROR] Fallo al sincronizar cabeceras de moves (refresh): %s", e)

        data_to_upsert = []
        for l in lines:
            data_to_upsert.append({
                'id': l['id'],
                'move_id': self._clean_m2o(l.get('move_id')),
                'partner_id': self._clean_m2o(l.get('partner_id')),
                'account_id': self._clean_m2o(l.get('account_id')),
                'name': l.get('name') or '',
                'date': self._clean_date(l.get('date')),
                'date_maturity': self._clean_date(l.get('date_maturity')),
                'amount_currency': l.get('amount_currency', 0),
                'amount_residual': l.get('amount_residual', 0),
                'currency_id': self._clean_m2o(l.get('currency_id')),
                'currency_name': self._clean_m2o_name(l.get('currency_id')),
                'debit': l.get('debit', 0),
                'credit': l.get('credit', 0),
                'balance': l.get('balance', 0),
                'parent_state': l.get('parent_state'),
                'matched_debit_ids': l.get('matched_debit_ids') or [],
                'matched_credit_ids': l.get('matched_credit_ids') or [],
                'reconciled': bool(l.get('reconciled', False)),
                'last_updated_at': datetime.now(timezone.utc).isoformat()
            })

        try:
            self.supabase.table('fact_move_lines').upsert(data_to_upsert).execute()
            return len(data_to_upsert)
        except Exception as e:
            logger.error("[ERROR] Fallo al guardar fact_move_lines (refresh): %s", e)
            return 0

    def refresh_move_lines_by_ids(self, line_ids):
        """Re-sincroniza líneas CxC concretas (p. ej. tras conciliación parcial)."""
        if not line_ids:
            return 0
        unique_ids = list({int(i) for i in line_ids if i})
        refreshed = 0
        for offset in range(0, len(unique_ids), PAGE_SIZE):
            batch_ids = unique_ids[offset:offset + PAGE_SIZE]
            lines = self._execute_kw(
                'account.move.line', 'read', [batch_ids],
                {'fields': self._MOVE_LINE_FIELDS},
            )
            refreshed += self._upsert_move_lines_from_odoo(lines or [])
        if refreshed:
            logger.info("[MOVE_LINES] %s líneas refrescadas por IDs explícitos", refreshed)
        return refreshed
        """IDs de fact_move_lines ya presentes en Supabase (para filtrar FKs)."""
        if not line_ids:
            return set()
        existing = set()
        chunk_size = 500
        for i in range(0, len(line_ids), chunk_size):
            chunk = line_ids[i:i + chunk_size]
            resp = self.supabase.table('fact_move_lines').select('id').in_('id', chunk).execute()
            existing.update(row['id'] for row in (resp.data or []))
        return existing

    def sync_partial_reconciles(self):
        """
        Sincroniza account.partial.reconcile hacia fact_partial_reconciles.
        Necesario para recalcular amount_residual_historical/paid_after_cutoff/
        paid_before_cutoff al vuelo según el date_cutoff que pida cada request
        (no se puede precalcular, ver app/collections/services.py::_get_reconciliation_amounts).

        Se acota a conciliaciones donde al menos una de las dos líneas
        (debit_move_id/credit_move_id) pertenece a una cuenta 12x de Cobranzas,
        para no traer todo el histórico contable de conciliaciones de la compañía.
        """
        logger.info("[PARTIAL_RECONCILES] Iniciando sincronización de conciliaciones...")
        last_sync = self.get_last_sync(SYNC_KEY_PARTIAL_RECONCILES)
        last_sync_odoo = _to_odoo_datetime(last_sync)

        domain = ['|'] + self._account_code_prefix_domain('debit_move_id.account_id.code') \
            + self._account_code_prefix_domain('credit_move_id.account_id.code')
        if last_sync_odoo:
            domain.append(('write_date', '>=', last_sync_odoo))
            logger.info("[PARTIAL_RECONCILES] Sync incremental desde write_date >= %s", last_sync_odoo)
        else:
            logger.info("[PARTIAL_RECONCILES] Sin sync previo registrado: se trae el histórico completo")

        # amount_currency/currency_id no existen en account.partial.reconcile de esta
        # instancia Odoo (amah producción); CollectionsService solo usa amount y max_date.
        fields = ['id', 'debit_move_id', 'credit_move_id', 'amount', 'max_date']

        reconcile_ids = self._search_all_ids('account.partial.reconcile', domain)

        if not reconcile_ids:
            logger.info("[PARTIAL_RECONCILES] No se encontraron conciliaciones nuevas/modificadas.")
            self.set_last_sync(SYNC_KEY_PARTIAL_RECONCILES, datetime.now(timezone.utc).isoformat())
            return

        sync_started_at = datetime.now(timezone.utc).isoformat()
        touched_line_ids = set()

        for offset in range(0, len(reconcile_ids), PAGE_SIZE):
            batch_ids = reconcile_ids[offset:offset + PAGE_SIZE]
            partials = self._execute_kw('account.partial.reconcile', 'read', [batch_ids], {'fields': fields})

            data_to_upsert = []
            for p in partials:
                debit_line_id = self._clean_m2o(p.get('debit_move_id'))
                credit_line_id = self._clean_m2o(p.get('credit_move_id'))
                if debit_line_id:
                    touched_line_ids.add(debit_line_id)
                if credit_line_id:
                    touched_line_ids.add(credit_line_id)
                data_to_upsert.append({
                    'id': p['id'],
                    'debit_move_line_id': debit_line_id,
                    'credit_move_line_id': credit_line_id,
                    'amount': p.get('amount', 0),
                    'amount_currency': 0,
                    'currency_id': None,
                    'max_date': self._clean_date(p.get('max_date')),
                    'last_updated_at': datetime.now(timezone.utc).isoformat()
                })

            if not data_to_upsert:
                continue

            try:
                self.supabase.table('fact_partial_reconciles').upsert(data_to_upsert).execute()
                logger.info("[PARTIAL_RECONCILES] %s conciliaciones sincronizadas (offset=%s)", len(data_to_upsert), offset)
            except Exception as e:
                logger.error("[ERROR] Fallo al guardar fact_partial_reconciles (offset=%s): %s", offset, e)

        if touched_line_ids:
            # Odoo no siempre actualiza write_date en account.move.line al conciliar;
            # refrescar las líneas tocadas mantiene amount_residual/reconciled al día.
            self.refresh_move_lines_by_ids(list(touched_line_ids))

        self.set_last_sync(SYNC_KEY_PARTIAL_RECONCILES, sync_started_at)

    def sync_accounts(self):
        """Sincroniza el catálogo de cuentas contables (account.account) a dim_accounts.
        Catálogo pequeño: se trae completo en cada corrida (sin watermark incremental)."""
        logger.info("[DIM_ACCOUNTS] Sincronizando catálogo de cuentas contables...")
        try:
            accounts = self._execute_kw(
                'account.account', 'search_read', [[]],
                {'fields': ['id', 'code', 'name', 'currency_id']}
            ) or []
            data_to_upsert = [{
                'id': a['id'],
                'code': a.get('code') or '',
                'name': a.get('name') or '',
                'currency_name': self._clean_m2o_name(a.get('currency_id')),
                'last_updated_at': datetime.now(timezone.utc).isoformat()
            } for a in accounts]
            if data_to_upsert:
                self.supabase.table('dim_accounts').upsert(data_to_upsert).execute()
            logger.info("[DIM_ACCOUNTS] %s cuentas sincronizadas", len(data_to_upsert))
            self.set_last_sync(SYNC_KEY_DIM_ACCOUNTS, datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.error("[ERROR] Fallo al sincronizar dim_accounts: %s", e)

    def sync_sales_channels(self):
        """Sincroniza agr.sales.channel a dim_sales_channels (catálogo pequeño, full sync)."""
        logger.info("[DIM_SALES_CHANNELS] Sincronizando canales de venta...")
        try:
            channels = self._execute_kw(
                'agr.sales.channel', 'search_read', [[]], {'fields': ['id', 'name']}
            ) or []
            data_to_upsert = [{
                'id': c['id'],
                'name': c.get('name') or '',
                'last_updated_at': datetime.now(timezone.utc).isoformat()
            } for c in channels]
            if data_to_upsert:
                self.supabase.table('dim_sales_channels').upsert(data_to_upsert).execute()
            logger.info("[DIM_SALES_CHANNELS] %s canales sincronizados", len(data_to_upsert))
            self.set_last_sync(SYNC_KEY_DIM_SALES_CHANNELS, datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.error("[ERROR] Fallo al sincronizar dim_sales_channels: %s", e)

    def sync_doc_types(self):
        """Sincroniza l10n_latam.document.type a dim_doc_types (catálogo pequeño, full sync)."""
        logger.info("[DIM_DOC_TYPES] Sincronizando tipos de documento LATAM...")
        try:
            doc_types = self._execute_kw(
                'l10n_latam.document.type', 'search_read', [[]], {'fields': ['id', 'name']}
            ) or []
            data_to_upsert = [{
                'id': d['id'],
                'name': d.get('name') or '',
                'last_updated_at': datetime.now(timezone.utc).isoformat()
            } for d in doc_types]
            if data_to_upsert:
                self.supabase.table('dim_doc_types').upsert(data_to_upsert).execute()
            logger.info("[DIM_DOC_TYPES] %s tipos de documento sincronizados", len(data_to_upsert))
            self.set_last_sync(SYNC_KEY_DIM_DOC_TYPES, datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.error("[ERROR] Fallo al sincronizar dim_doc_types: %s", e)

    def sync_credit_customers(self):
        """
        Sincroniza agr.credit.customer (sub_channel_id + partner_groups_ids) a
        dim_credit_customers. Resuelve los nombres de agr.groups en el momento
        del sync y los guarda ya concatenados (ver nota de diseño en
        scripts/etl/supabase_schema_collections.sql), evitando modelar una
        dimensión agr.groups separada solo para este único uso.
        """
        logger.info("[DIM_CREDIT_CUSTOMERS] Sincronizando clientes de crédito...")
        try:
            rows = self._execute_kw(
                'agr.credit.customer', 'search_read', [[]],
                {'fields': ['partner_id', 'partner_groups_ids', 'sub_channel_id']}
            ) or []

            group_ids = set()
            for r in rows:
                group_ids.update(r.get('partner_groups_ids') or [])

            group_name_map = {}
            if group_ids:
                groups = self._execute_kw('agr.groups', 'read', [list(group_ids)], {'fields': ['id', 'name']})
                group_name_map = {g['id']: g.get('name', '') for g in groups}

            # Odoo puede devolver varias filas agr.credit.customer para el mismo partner_id;
            # deduplicar antes del upsert para evitar error 21000 de Postgres.
            by_partner = {}
            for r in rows:
                partner_id = self._clean_m2o(r.get('partner_id'))
                if not partner_id:
                    continue
                group_names = [group_name_map[gid] for gid in (r.get('partner_groups_ids') or []) if gid in group_name_map]
                by_partner[partner_id] = {
                    'partner_id': partner_id,
                    'sub_channel_name': self._clean_m2o_name(r.get('sub_channel_id')),
                    'partner_groups_display': ', '.join(group_names),
                    'last_updated_at': datetime.now(timezone.utc).isoformat()
                }
            data_to_upsert = list(by_partner.values())

            if data_to_upsert:
                self.supabase.table('dim_credit_customers').upsert(data_to_upsert).execute()
            logger.info("[DIM_CREDIT_CUSTOMERS] %s clientes de crédito sincronizados", len(data_to_upsert))
            self.set_last_sync(SYNC_KEY_DIM_CREDIT_CUSTOMERS, datetime.now(timezone.utc).isoformat())
        except Exception as e:
            logger.error("[ERROR] Fallo al sincronizar dim_credit_customers: %s", e)

    def sync_sale_orders(self):
        """
        Sincroniza sale.order (sub_channel_id + tag_ids -> método de pago) a
        dim_sale_orders, de forma incremental por write_date (a diferencia de
        las demás dimensiones, sale.order puede ser una tabla grande).
        """
        logger.info("[DIM_SALE_ORDERS] Iniciando sincronización de órdenes de venta...")
        last_sync = self.get_last_sync(SYNC_KEY_DIM_SALE_ORDERS)
        last_sync_odoo = _to_odoo_datetime(last_sync)

        domain = []
        if last_sync_odoo:
            domain.append(('write_date', '>=', last_sync_odoo))
            logger.info("[DIM_SALE_ORDERS] Sync incremental desde write_date >= %s", last_sync_odoo)
        else:
            logger.info("[DIM_SALE_ORDERS] Sin sync previo registrado: se trae el histórico completo")

        fields = ['id', 'sub_channel_id', 'tag_ids']
        order_ids = self._search_all_ids('sale.order', domain)

        if not order_ids:
            logger.info("[DIM_SALE_ORDERS] No se encontraron órdenes nuevas/modificadas.")
            self.set_last_sync(SYNC_KEY_DIM_SALE_ORDERS, datetime.now(timezone.utc).isoformat())
            return

        sync_started_at = datetime.now(timezone.utc).isoformat()

        for offset in range(0, len(order_ids), PAGE_SIZE):
            batch_ids = order_ids[offset:offset + PAGE_SIZE]
            orders = self._execute_kw('sale.order', 'read', [batch_ids], {'fields': fields})

            tag_ids_set = set()
            for o in orders:
                tag_ids_set.update(o.get('tag_ids') or [])
            tag_name_map = {}
            if tag_ids_set:
                tags = self._execute_kw('crm.tag', 'read', [list(tag_ids_set)], {'fields': ['id', 'name']})
                tag_name_map = {t['id']: t.get('name', '') for t in tags}
                try:
                    self.supabase.table('dim_payment_tags').upsert([
                        {'id': t['id'], 'name': t.get('name', ''), 'last_updated_at': datetime.now(timezone.utc).isoformat()}
                        for t in tags
                    ]).execute()
                except Exception as e:
                    logger.error("[ERROR] Fallo al guardar dim_payment_tags (offset=%s): %s", offset, e)

            data_to_upsert = []
            for o in orders:
                order_tag_ids = o.get('tag_ids') or []
                tag_names = [tag_name_map[tid] for tid in order_tag_ids if tid in tag_name_map]
                data_to_upsert.append({
                    'id': o['id'],
                    'sub_channel_name': self._clean_m2o_name(o.get('sub_channel_id')),
                    'tag_ids': order_tag_ids,
                    'payment_method_display': ', '.join(tag_names),
                    'last_updated_at': datetime.now(timezone.utc).isoformat()
                })

            try:
                self.supabase.table('dim_sale_orders').upsert(data_to_upsert).execute()
                logger.info("[DIM_SALE_ORDERS] %s órdenes sincronizadas (offset=%s)", len(data_to_upsert), offset)
            except Exception as e:
                logger.error("[ERROR] Fallo al guardar dim_sale_orders (offset=%s): %s", offset, e)

        self.set_last_sync(SYNC_KEY_DIM_SALE_ORDERS, sync_started_at)


def run_etl():
    """Función principal para ejecutar el ETL. Invocada por la tarea Celery run_etl_sync."""
    logger.info("=" * 50)
    logger.info("INICIANDO ETL: %s", datetime.now(timezone.utc))
    logger.info("=" * 50)

    try:
        syncer = OdooSync()

        syncer.sync_moves()    # Trae Facturas y Notas de Crédito (incremental)
        syncer.sync_letters()  # Trae Letras y las une (incremental)

        # --- Piloto Cobranzas (Fase 3): dimensiones primero, luego hechos que las referencian ---
        syncer.sync_accounts()          # dim_accounts
        syncer.sync_sales_channels()    # dim_sales_channels
        syncer.sync_doc_types()         # dim_doc_types
        syncer.sync_credit_customers()  # dim_credit_customers
        syncer.sync_sale_orders()       # dim_sale_orders (incremental)
        syncer.sync_move_lines()        # fact_move_lines (incremental)
        syncer.sync_partial_reconciles()  # fact_partial_reconciles (incremental)

        logger.info("[SUCCESS] ETL Completado Exitosamente")

    except Exception as e:
        logger.error("[CRITICAL ERROR] ETL Falló: %s", e)
        logger.error(traceback.format_exc())
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    _load_env_if_standalone()
    run_etl()
