# -*- coding: utf-8 -*-
"""
Script ETL (Extract, Transform, Load) para sincronizar Odoo -> Supabase.
Maneja Facturas, Notas de Crédito y Letras usando Threading.
"""

import os
import threading
import time
import xmlrpc.client
import traceback
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Cargar entorno
env_prod = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.produccion'))
env_dev = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.desarrollo'))

if os.path.exists(env_prod):
    load_dotenv(env_prod)
    print(f"[INIT] Cargando configuración desde: .env.produccion")
else:
    load_dotenv(env_dev)
    print(f"[INIT] Cargando configuración desde: .env.desarrollo")

# Configuración (limpiar comillas si existen)
def get_env_clean(key):
    val = os.getenv(key)
    return val.replace('"', '').replace("'", "") if val else None

ODOO_URL = get_env_clean('ODOO_URL')
ODOO_DB = get_env_clean('ODOO_DB')
ODOO_USER = get_env_clean('ODOO_USER')
ODOO_PASSWORD = get_env_clean('ODOO_PASSWORD')

SUPABASE_URL = get_env_clean('SUPABASE_URL')
SUPABASE_KEY = get_env_clean('SUPABASE_KEY')

class OdooSync:
    def __init__(self):
        self.common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        self.uid = self.common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        self.models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print(f"[INIT] Conectado a Odoo UID: {self.uid}")

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
        if not partner_ids: return
        
        print(f"[PARTNERS] Sincronizando {len(partner_ids)} socios...")
        fields = ['id', 'name', 'vat', 'country_id', 'state_id', 'is_company', 'email', 'phone', 'supplier_rank', 'customer_rank']
        partners = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'res.partner', 'read', [list(partner_ids)], {'fields': fields})
        
        data_to_upsert = []
        for p in partners:
            # Obtener nombres de relaciones (country, state) requiere otra llamada o asumimos ids por ahora
            # Para simplificar, guardamos solo códigos/nombres si los tenemos, o el ID
            state_name = p['state_id'][1] if p.get('state_id') else None
            country_code = None # Requeriría fetch extra, lo dejamos pendiente
            
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
                'last_updated_at': datetime.now().isoformat()
            })
        
        # Batch upsert
        if data_to_upsert:
            self.supabase.table('dim_partners').upsert(data_to_upsert).execute()
            print(f"[PARTNERS] ✓ {len(data_to_upsert)} actualizados")

    def sync_moves(self):
        """
        Sincroniza Facturas y Notas de Crédito (In/Out).
        """
        print("[MOVES] Iniciando sincronización de Movimientos...")
        domain = [
            ('state', 'in', ['posted', 'draft']),
            ('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund'])
        ]
        # Campos a leer
        fields = [
            'id', 'name', 'ref', 'date', 'invoice_date', 'invoice_date_due', 
            'state', 'move_type', 'payment_state', 'currency_id', 
            'amount_total', 'amount_residual', 'amount_untaxed', 
            'partner_id', 'reversed_entry_id'
        ]
        
        # Buscar IDs (Limitamos a 1000 para prueba, quitar limite en prod)
        move_ids = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'search', [domain], {'limit': 500})
        
        if not move_ids:
            print("[MOVES] No se encontraron movimientos.")
            return

        # Leer datos
        moves = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'read', [move_ids], {'fields': fields})
        
        # Recolectar Partners para sincronizar primero (Integridad Referencial)
        partner_ids = set()
        for m in moves:
            pid = self._clean_m2o(m.get('partner_id'))
            if pid: partner_ids.add(pid)
            
        self.sync_partners(partner_ids)
        
        # Preparar datos para Supabase
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
                'last_updated_at': datetime.now().isoformat()
            })
            
        # Batch Upsert (Supabase maneja batches, pero mejor no excederse)
        try:
            self.supabase.table('fact_moves').upsert(data_to_upsert).execute()
            print(f"[MOVES] ✓ {len(data_to_upsert)} movimientos sincronizados")
        except Exception as e:
            print(f"[ERROR] Fallo al guardar moves: {e}")

    def sync_letters(self):
        """
        Sincroniza Letras de Cambio y sus relaciones con facturas.
        """
        print("[LETTERS] Iniciando sincronización de Letras...")
        # Buscar registros que tengan número de letra
        domain = [('l10n_latam_boe_number', '!=', False)]
        fields = [
            'id', 'name', 'l10n_latam_boe_number', 'state', 'date', 
            'invoice_date_due', 'amount_total', 'partner_id', 'move_type',
            'bill_form_invoices' # Campo CLAVE
        ]
        
        letter_ids = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'search', [domain], {'limit': 500})
        
        if not letter_ids:
            print("[LETTERS] No se encontraron letras.")
            return
            
        letters = self.models.execute_kw(ODOO_DB, self.uid, ODOO_PASSWORD, 'account.move', 'read', [letter_ids], {'fields': fields})
        
        # Sincronizar partners de letras
        partner_ids = set()
        for l in letters:
            pid = self._clean_m2o(l.get('partner_id'))
            if pid: partner_ids.add(pid)
        self.sync_partners(partner_ids)
        
        letters_to_upsert = []
        relations_to_upsert = []
        
        for l in letters:
            # 1. Guardar Letra
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
                'last_updated_at': datetime.now().isoformat()
            })
            
            # 2. Procesar Relaciones (bill_form_invoices)
            # bill_form_invoices es una lista de IDs de facturas: [123, 456]
            invoice_ids = l.get('bill_form_invoices', [])
            for inv_id in invoice_ids:
                relations_to_upsert.append({
                    'letter_id': l['id'],
                    'move_id': inv_id
                })
        
        try:
            self.supabase.table('fact_letters').upsert(letters_to_upsert).execute()
            print(f"[LETTERS] ✓ {len(letters_to_upsert)} letras sincronizadas")
            
            # Guardar relaciones (puede fallar si el move_id no existe en fact_moves, 
            # por integridad referencial deberíamos asegurar que las moves existan, 
            # pero si corremos sync_moves antes, debería estar OK)
            if relations_to_upsert:
                self.supabase.table('rel_letter_moves').upsert(relations_to_upsert).execute()
                print(f"[RELATIONS] ✓ {len(relations_to_upsert)} relaciones letra-factura creadas")
                
        except Exception as e:
            print(f"[ERROR] Fallo al guardar letras/relaciones: {e}")

def run_etl():
    """Función principal para ejecutar el ETL"""
    print("="*50)
    print(f"INICIANDO ETL: {datetime.now()}")
    print("="*50)
    
    try:
        syncer = OdooSync()
        
        # Usar Threads para simular paralelismo (aunque Python tiene GIL, para I/O network sirve)
        # Pero Odoo XMLRPC puede saturarse, mejor secuencial por seguridad primero
        syncer.sync_moves() # Trae Facturas y Notas de Crédito
        syncer.sync_letters() # Trae Letras y las une
        
        print("\n[SUCCESS] ETL Completado Exitosamente")
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] ETL Falló: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    run_etl()

