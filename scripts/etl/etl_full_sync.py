# -*- coding: utf-8 -*-
"""
Script ETL Completo: Sincroniza Facturas -> Planillas -> Letras
(Simplificado: Sin tabla de Pedidos)
"""

import os
import xmlrpc.client
import traceback
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Cargar entorno
# Ajustar path para encontrar .env.desarrollo desde scripts/etl/
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.desarrollo'))
load_dotenv(env_path)

ODOO_URL = os.getenv('ODOO_URL')
ODOO_DB = os.getenv('ODOO_DB')
ODOO_USER = os.getenv('ODOO_USER')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

class OdooETL:
    def __init__(self):
        self.common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        self.uid = self.common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        self.models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[INIT] Conectado a Odoo UID: {self.uid}")

    def _clean_m2o(self, field):
        return field[0] if isinstance(field, list) and field else None

    def _clean_date(self, date_str):
        return date_str if date_str else None

    def sync_partners(self, partner_ids):
        """Sincroniza socios (dim_partners)"""
        if not partner_ids: return
        print(f"[PARTNERS] Sincronizando {len(partner_ids)} socios...")
        
        chunks = [list(partner_ids)[i:i + 500] for i in range(0, len(partner_ids), 500)]
        
        for chunk in chunks:
            partners = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'res.partner', 'read', 
                [chunk], 
                {'fields': ['id', 'name', 'vat', 'state_id', 'is_company', 'email', 'phone']}
            )
            
            data = []
            for p in partners:
                state_name = p['state_id'][1] if p.get('state_id') else None
                data.append({
                    'id': p['id'],
                    'name': p['name'],
                    'vat': p.get('vat'),
                    'state_name': state_name,
                    'is_company': p.get('is_company'),
                    'email': str(p.get('email') or ''),
                    'phone': str(p.get('phone') or ''),
                    'last_updated_at': datetime.now().isoformat()
                })
            self.supabase.table('dim_partners').upsert(data).execute()

    def sync_moves(self):
        """Sincroniza Facturas y Notas de Crédito (fact_moves)"""
        print("[MOVES] Sincronizando Movimientos...")
        domain = [('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'])]
        # Aumentamos el límite para traer más histórico
        ids = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'search', 
            [domain], {'limit': 2000, 'order': 'invoice_date desc'})
        
        moves = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'read', 
            [ids], 
            {'fields': ['id', 'name', 'ref', 'date', 'invoice_date', 'invoice_date_due', 
                       'state', 'move_type', 'payment_state', 'amount_total', 
                       'amount_residual', 'partner_id', 'invoice_origin']}
        )
        
        p_ids = {self._clean_m2o(m['partner_id']) for m in moves if m.get('partner_id')}
        self.sync_partners(p_ids)
        
        data = []
        for m in moves:
            data.append({
                'id': m['id'],
                'name': m['name'],
                'ref': m.get('ref'),
                'date': self._clean_date(m.get('date')),
                'invoice_date': self._clean_date(m.get('invoice_date')),
                'invoice_date_due': self._clean_date(m.get('invoice_date_due')),
                'state': m.get('state'),
                'move_type': m.get('move_type'),
                'payment_state': m.get('payment_state'),
                'invoice_origin': m.get('invoice_origin'), # Aquí va el Pedido (Sxxxxx)
                'amount_total': m.get('amount_total'),
                'amount_residual': m.get('amount_residual'),
                'partner_id': self._clean_m2o(m.get('partner_id')),
                'last_updated_at': datetime.now().isoformat()
            })
            
        # Batch upsert en chunks de 1000 para no saturar la API
        chunk_size = 1000
        for i in range(0, len(data), chunk_size):
            batch = data[i:i + chunk_size]
            self.supabase.table('fact_moves').upsert(batch).execute()
            
        print(f"[MOVES] ✓ {len(data)} movimientos sincronizados")

    def sync_bill_forms_and_letters(self):
        """Sincroniza Planillas (fact_bill_forms) y sus Letras (fact_letters)"""
        print("[BILL FORMS] Sincronizando Planillas y Letras...")
        
        # 1. Traer Planillas
        bf_ids = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.bill.form', 'search', 
            [[]], {'limit': 500, 'order': 'id desc'})
        
        if not bf_ids: return

        bfs = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.bill.form', 'read', 
            [bf_ids], 
            {'fields': ['id', 'name', 'state', 'amount_total', 'partner_id', 'invoice_ids', 'move_ids']}
        )
        
        p_ids = {self._clean_m2o(bf['partner_id']) for bf in bfs if bf.get('partner_id')}
        self.sync_partners(p_ids)
        
        bf_data = []
        rel_data = [] # Relación Planilla <-> Factura
        all_letter_ids = []
        
        for bf in bfs:
            bf_id = bf['id']
            bf_data.append({
                'id': bf_id,
                'name': bf['name'],
                'state': bf['state'],
                'amount_total': bf['amount_total'],
                'partner_id': self._clean_m2o(bf.get('partner_id')),
                'last_updated_at': datetime.now().isoformat()
            })
            
            for inv_id in bf.get('invoice_ids', []):
                rel_data.append({'bill_form_id': bf_id, 'move_id': inv_id})
            
            all_letter_ids.extend(bf.get('move_ids', []))

        self.supabase.table('fact_bill_forms').upsert(bf_data).execute()
        print(f"[BILL FORMS] ✓ {len(bf_data)} planillas guardadas")
        
        if rel_data:
            self.supabase.table('rel_bill_form_invoices').upsert(rel_data).execute()
        
        print(f"[LETTERS] Sincronizando {len(all_letter_ids)} letras...")
        if not all_letter_ids: return
        
        letters = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'read', 
            [list(set(all_letter_ids))], 
            {'fields': ['id', 'name', 'l10n_latam_boe_number', 'state', 'date', 'invoice_date_due', 'amount_total', 'partner_id', 'move_type', 'bill_form_id']}
        )
        
        letter_data = []
        for l in letters:
            letter_data.append({
                'id': l['id'],
                'name': l['name'],
                'boe_number': l.get('l10n_latam_boe_number'),
                'state': l.get('state'),
                'date': self._clean_date(l.get('date')),
                'due_date': self._clean_date(l.get('invoice_date_due')),
                'amount_total': l.get('amount_total'),
                'partner_id': self._clean_m2o(l.get('partner_id')),
                'move_type': l.get('move_type'),
                'bill_form_id': self._clean_m2o(l.get('bill_form_id')),
                'last_updated_at': datetime.now().isoformat()
            })
            
        self.supabase.table('fact_letters').upsert(letter_data).execute()
        print(f"[LETTERS] ✓ {len(letter_data)} letras guardadas")

def run():
    etl = OdooETL()
    # sync_orders removido
    etl.sync_moves() # Trae el invoice_origin (Pedido)
    etl.sync_bill_forms_and_letters()

if __name__ == '__main__':
    run()
