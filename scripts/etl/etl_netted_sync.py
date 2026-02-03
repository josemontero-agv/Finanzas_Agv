# -*- coding: utf-8 -*-
"""
Script ETL Neteado: Sincroniza Odoo -> Supabase incluyendo líneas y conciliaciones.
Soporta reportes agrupados (Neteados) y Matching Backwards.
"""

import os
import xmlrpc.client
import traceback
import ssl  # Añadido para bypass SSL
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# Bypass SSL para entornos corporativos/proxies
ssl._create_default_https_context = ssl._create_unverified_context

# Cargar entorno de manera robusta
def load_env():
    possible_paths = [
        # Nuevos archivos separados por servicio
        os.path.join(os.getcwd(), '.env.supabase.produccion'),
        os.path.join(os.getcwd(), '.env.produccion'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.supabase.produccion')),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.produccion')),
        # Desarrollo
        os.path.join(os.getcwd(), '.env.supabase.desarrollo'),
        os.path.join(os.getcwd(), '.env.desarrollo')
    ]
    for path in possible_paths:
        if os.path.exists(path):
            load_dotenv(path, override=True)
            print(f"[ENV] Cargado: {path}")
            # No retornamos True aquí para permitir cargar múltiples archivos (Odoo + Supabase)
    return True

load_env()

ODOO_URL = os.getenv('ODOO_URL', '').replace('"', '').replace("'", "")
ODOO_DB = os.getenv('ODOO_DB', '').replace('"', '').replace("'", "")
ODOO_USER = os.getenv('ODOO_USER', '').replace('"', '').replace("'", "")
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', '').replace('"', '').replace("'", "")

SUPABASE_URL = os.getenv('SUPABASE_URL', '').replace('"', '').replace("'", "")
SUPABASE_KEY = os.getenv('SUPABASE_KEY', '').replace('"', '').replace("'", "")

class OdooNettedSync:
    def __init__(self):
        self.common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        self.uid = self.common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        self.models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[INIT] Conectado a Odoo UID: {self.uid}")

    def _clean_m2o(self, field):
        return field[0] if isinstance(field, list) and field else None

    def _clean_val(self, value):
        """Limpia valores de Odoo (False -> None)"""
        if value is False:
            return None
        return value

    def sync_partners(self, partner_ids):
        if not partner_ids: return
        partner_ids = list(set(partner_ids))
        print(f"[PARTNERS] Sincronizando {len(partner_ids)} socios...")
        
        chunks = [partner_ids[i:i + 100] for i in range(0, len(partner_ids), 100)]
        for chunk in chunks:
            partners = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'res.partner', 'read', 
                [chunk], 
                {'fields': ['id', 'name', 'vat', 'state_id', 'is_company', 'email', 'phone', 'supplier_rank', 'customer_rank']}
            )
            data = []
            for p in partners:
                data.append({
                    'id': p['id'],
                    'name': p['name'],
                    'vat': p.get('vat'),
                    'state_name': p['state_id'][1] if p.get('state_id') else None,
                    'is_company': p.get('is_company'),
                    'email': str(p.get('email') or ''),
                    'phone': str(p.get('phone') or ''),
                    'supplier_rank': p.get('supplier_rank', 0),
                    'customer_rank': p.get('customer_rank', 0),
                    'last_updated_at': datetime.now().isoformat()
                })
            self.supabase.table('dim_partners').upsert(data).execute()

    def sync_financial_data(self, days_back=30):
        """Sincroniza Facturas, Líneas y Conciliaciones"""
        print(f"[SYNC] Iniciando sincronización de datos financieros (últimos {days_back} días)...")
        
        limit_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # 1. Sync account.move (Cabeceras)
        move_domain = [
            ('date', '>=', limit_date),
            ('move_type', 'in', ['in_invoice', 'in_refund', 'out_invoice', 'out_refund', 'entry'])
        ]
        move_ids = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'search', [move_domain])
        
        if not move_ids:
            print("[SYNC] No hay movimientos nuevos.")
            return

        moves = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'read', 
            [move_ids], 
            {'fields': ['id', 'name', 'ref', 'date', 'invoice_date', 'invoice_date_due', 'state', 'move_type', 'payment_state', 'currency_id', 'amount_total', 'amount_residual', 'partner_id']}
        )
        
        # Sync Partners primero
        p_ids = [self._clean_m2o(m['partner_id']) for m in moves if m.get('partner_id')]
        self.sync_partners(p_ids)
        
        move_data = []
        for m in moves:
            move_data.append({
                'id': m['id'],
                'name': m['name'],
                'ref': self._clean_val(m.get('ref')),
                'date': self._clean_val(m.get('date')),
                'invoice_date': self._clean_val(m.get('invoice_date')),
                'invoice_date_due': self._clean_val(m.get('invoice_date_due')),
                'state': m.get('state'),
                'move_type': m.get('move_type'),
                'payment_state': m.get('payment_state'),
                'currency_id': self._clean_m2o(m.get('currency_id')),
                'amount_total': m.get('amount_total'),
                'amount_residual': m.get('amount_residual'),
                'partner_id': self._clean_m2o(m.get('partner_id')),
                'last_updated_at': datetime.now().isoformat()
            })
        self.supabase.table('fact_moves').upsert(move_data).execute()
        print(f"[MOVES] ✓ {len(move_data)} cabeceras sincronizadas")

        # 2. Sync account.move.line (Líneas de las cuentas 12, 42, 43, 67, 77)
        line_domain = [
            ('move_id', 'in', move_ids),
            '|', '|', '|', 
            ('account_id.code', '=like', '12%'),
            ('account_id.code', '=like', '42%'),
            ('account_id.code', '=like', '43%'),
            ('account_id.code', '=like', '67%'),
            ('account_id.code', '=like', '77%')
        ]
        line_ids = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move.line', 'search', [line_domain])
        
        if line_ids:
            lines = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move.line', 'read', 
                [line_ids], 
                {'fields': ['id', 'move_id', 'partner_id', 'account_id', 'name', 'date', 'date_maturity', 'debit', 'credit', 'balance', 'amount_residual', 'amount_currency', 'currency_id', 'reconciled', 'full_reconcile_id', 'matched_debit_ids', 'matched_credit_ids']}
            )
            
            line_data = []
            apr_ids = set()
            for l in lines:
                line_data.append({
                    'id': l['id'],
                    'move_id': self._clean_m2o(l.get('move_id')),
                    'partner_id': self._clean_m2o(l.get('partner_id')),
                    'account_id': self._clean_m2o(l.get('account_id')),
                    'account_code': l['account_id'][1].split(' ')[0] if isinstance(l.get('account_id'), list) else None,
                    'name': self._clean_val(l.get('name')),
                    'date': self._clean_val(l.get('date')),
                    'date_maturity': self._clean_val(l.get('date_maturity')),
                    'debit': l.get('debit'),
                    'credit': l.get('credit'),
                    'balance': l.get('balance'),
                    'amount_residual': l.get('amount_residual'),
                    'amount_currency': l.get('amount_currency'),
                    'currency_id': self._clean_m2o(l.get('currency_id')),
                    'reconciled': l.get('reconciled'),
                    'full_reconcile_id': self._clean_m2o(l.get('full_reconcile_id')),
                    'last_updated_at': datetime.now().isoformat()
                })
                # Recolectar IDs de conciliaciones parciales
                if l.get('matched_debit_ids'): apr_ids.update(l['matched_debit_ids'])
                if l.get('matched_credit_ids'): apr_ids.update(l['matched_credit_ids'])
            
            # Upsert lines in chunks
            for i in range(0, len(line_data), 500):
                self.supabase.table('fact_move_lines').upsert(line_data[i:i+500]).execute()
            print(f"[LINES] ✓ {len(line_data)} líneas sincronizadas")

            # 3. Sync account.partial.reconcile
            if apr_ids:
                aprs = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.partial.reconcile', 'read', 
                    [list(apr_ids)], 
                    {'fields': ['id', 'debit_move_id', 'credit_move_id', 'amount', 'amount_currency', 'currency_id', 'max_date']}
                )
                apr_data = []
                for a in aprs:
                    apr_data.append({
                        'id': a['id'],
                        'debit_move_line_id': self._clean_m2o(a.get('debit_move_id')),
                        'credit_move_line_id': self._clean_m2o(a.get('credit_move_id')),
                        'amount': a.get('amount'),
                        'amount_currency': a.get('amount_currency'),
                        'currency_id': self._clean_m2o(a.get('currency_id')),
                        'max_date': self._clean_val(a.get('max_date')),
                        'last_updated_at': datetime.now().isoformat()
                    })
                self.supabase.table('fact_partial_reconciles').upsert(apr_data).execute()
                print(f"[RECONCILES] ✓ {len(apr_data)} conciliaciones parciales sincronizadas")

def run():
    sync = OdooNettedSync()
    sync.sync_financial_data(days_back=90) # Sincronizar últimos 3 meses

if __name__ == '__main__':
    run()

