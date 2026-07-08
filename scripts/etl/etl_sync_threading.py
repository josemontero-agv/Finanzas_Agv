# -*- coding: utf-8 -*-
"""
Script ETL (Extract, Transform, Load) para sincronizar Odoo -> Supabase.
Maneja Facturas, Notas de Crédito y Letras.

Sincronización incremental: cada modelo lleva su propia marca de agua (watermark) en la
tabla `etl_sync_state` de Supabase (ver scripts/etl/supabase_schema_etl_state.sql). Si ya
existe un último sync exitoso, solo se traen registros con `write_date` posterior; si no,
se trae el histórico completo paginando en lotes de PAGE_SIZE.
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

    def _clean_date(self, date_str):
        """Asegura formato fecha"""
        return date_str if date_str else None

    def sync_partners(self, partner_ids):
        """Sincroniza socios específicos a dim_partners"""
        if not partner_ids:
            return

        logger.info("[PARTNERS] Sincronizando %s socios...", len(partner_ids))
        fields = ['id', 'name', 'vat', 'country_id', 'state_id', 'is_company', 'email', 'phone', 'supplier_rank', 'customer_rank']
        partners = self._execute_kw('res.partner', 'read', [list(partner_ids)], {'fields': fields})

        data_to_upsert = []
        for p in partners:
            state_name = p['state_id'][1] if p.get('state_id') else None

            data_to_upsert.append({
                'id': p['id'],
                'name': p['name'],
                'vat': p['vat'],
                'state_name': state_name,
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

        fields = [
            'id', 'name', 'ref', 'date', 'invoice_date', 'invoice_date_due',
            'state', 'move_type', 'payment_state', 'currency_id',
            'amount_total', 'amount_residual', 'amount_untaxed',
            'partner_id', 'reversed_entry_id'
        ]

        move_ids = self._search_all_ids('account.move', domain)

        if not move_ids:
            logger.info("[MOVES] No se encontraron movimientos nuevos/modificados.")
            self.set_last_sync(SYNC_KEY_MOVES, datetime.now(timezone.utc).isoformat())
            return

        sync_started_at = datetime.now(timezone.utc).isoformat()

        for offset in range(0, len(move_ids), PAGE_SIZE):
            batch_ids = move_ids[offset:offset + PAGE_SIZE]
            moves = self._execute_kw('account.move', 'read', [batch_ids], {'fields': fields})

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
                    'amount_total': m.get('amount_total', 0),
                    'amount_residual': m.get('amount_residual', 0),
                    'amount_untaxed': m.get('amount_untaxed', 0),
                    'partner_id': self._clean_m2o(m.get('partner_id')),
                    'reversed_entry_id': self._clean_m2o(m.get('reversed_entry_id')),
                    'last_updated_at': datetime.now(timezone.utc).isoformat()
                })

            try:
                self.supabase.table('fact_moves').upsert(data_to_upsert).execute()
                logger.info("[MOVES] %s movimientos sincronizados (offset=%s)", len(data_to_upsert), offset)
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


def run_etl():
    """Función principal para ejecutar el ETL. Invocada por la tarea Celery run_etl_sync."""
    logger.info("=" * 50)
    logger.info("INICIANDO ETL: %s", datetime.now(timezone.utc))
    logger.info("=" * 50)

    try:
        syncer = OdooSync()

        syncer.sync_moves()    # Trae Facturas y Notas de Crédito (incremental)
        syncer.sync_letters()  # Trae Letras y las une (incremental)

        logger.info("[SUCCESS] ETL Completado Exitosamente")

    except Exception as e:
        logger.error("[CRITICAL ERROR] ETL Falló: %s", e)
        logger.error(traceback.format_exc())
        raise


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    _load_env_if_standalone()
    run_etl()
