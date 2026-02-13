# -*- coding: utf-8 -*-
"""
Script de TRAZABILIDAD DE DOCUMENTOS.
Rastrea el flujo: Pedido -> Factura -> Planilla -> Letras
"""

import xmlrpc.client
import os
import sys
# Añadir raíz al path para importar módulos si fuera necesario, 
# pero usaremos xmlrpc directo para evitar dependencias.
from dotenv import load_dotenv

def trace_flow(invoice_name=None):
    # Cargar env desde dos directorios arriba (estamos en scripts/investigation)
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env.produccion'))
    load_dotenv(env_path)
    
    url = os.getenv('ODOO_URL')
    db = os.getenv('ODOO_DB')
    username = os.getenv('ODOO_USER')
    password = os.getenv('ODOO_PASSWORD')
    
    if not all([url, db, username, password]):
        print("[ERROR] Faltan credenciales")
        return

    print(f"Conectando a {url}...")
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        if not uid:
            print("[ERROR] Auth fallida")
            return
        
        print("[OK] Conectado")
        print("="*60)
        print("TRAZABILIDAD DE DOCUMENTOS")
        print("="*60)

        # 1. Buscar una Factura (Invoice) con Letras asociadas
        # Usamos la pista de bill_form_id que vimos antes
        print("\n[1] Buscando factura con Planilla asociada...")
        
        # Buscar una factura que tenga bill_form_id seteado (si existe el campo)
        # O buscar una planilla y ver sus facturas
        
        # Estrategia: Buscar una Planilla reciente y desglosarla hacia atrás (Factura) y adelante (Letras)
        bill_forms = models.execute_kw(db, uid, password, 'account.bill.form', 'search_read', 
            [[]], 
            {'fields': ['name', 'invoice_ids', 'move_ids', 'state'], 'limit': 1, 'order': 'id desc'}
        )
        
        if not bill_forms:
            print("No se encontraron Planillas de Letras.")
            return

        bf = bill_forms[0]
        print(f"\n📍 PLANILLA ENCONTRADA: {bf['name']} (ID: {bf['id']})")
        print(f"   Estado: {bf['state']}")
        
        # 2. Rastrear hacia atrás: FACTURAS
        invoice_ids = bf.get('invoice_ids', [])
        print(f"\n   ⬆️ FACTURAS ORIGEN ({len(invoice_ids)}):")
        
        if invoice_ids:
            invoices = models.execute_kw(db, uid, password, 'account.move', 'read', 
                [invoice_ids], 
                {'fields': ['name', 'invoice_origin', 'amount_total', 'state', 'payment_state']}
            )
            
            for inv in invoices:
                print(f"      📄 Factura: {inv['name']} | Total: {inv['amount_total']} | Estado: {inv['state']}")
                
                # 3. Rastrear hacia atrás: PEDIDOS
                origin = inv.get('invoice_origin')
                if origin:
                    print(f"         ⬆️ Pedido Origen: {origin}")
                    # Intentar buscar el Sale Order
                    sos = models.execute_kw(db, uid, password, 'sale.order', 'search_read', 
                        [[('name', '=', origin)]], 
                        {'fields': ['name', 'date_order', 'amount_total', 'state']}
                    )
                    if sos:
                        so = sos[0]
                        print(f"            🛒 Sale Order: {so['name']} | Fecha: {so['date_order']} | Estado: {so['state']}")
                else:
                    print("         ⚠️ Sin documento origen (manual o importado)")

        # 4. Rastrear hacia adelante: LETRAS
        move_ids = bf.get('move_ids', [])
        print(f"\n   ⬇️ LETRAS GENERADAS ({len(move_ids)}):")
        
        if move_ids:
            letters = models.execute_kw(db, uid, password, 'account.move', 'read', 
                [move_ids], 
                {'fields': ['name', 'l10n_latam_boe_number', 'amount_total', 'state', 'date', 'invoice_date_due']}
            )
            
            for l in letters:
                print(f"      🧾 Letra: {l['name']}") 
                print(f"         Núm. BOE: {l.get('l10n_latam_boe_number')}")
                print(f"         Monto: {l['amount_total']}")
                print(f"         Vencimiento: {l['invoice_date_due']}")
                print(f"         Estado: {l['state']}")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    trace_flow()

