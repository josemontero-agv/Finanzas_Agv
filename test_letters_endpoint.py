# -*- coding: utf-8 -*-
"""Script para probar el endpoint de letras directamente"""

import sys
import os
import json
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.core.odoo import OdooRepository
from app.letters.letters_service import LettersService

def test_endpoint():
    app = create_app('development')
    
    with app.app_context():
        try:
            repo = OdooRepository(
                url=app.config['ODOO_URL'],
                db=app.config['ODOO_DB'],
                username=app.config['ODOO_USER'],
                password=app.config['ODOO_PASSWORD']
            )
            
            if not repo.is_connected():
                print("[ERROR] No hay conexión a Odoo")
                return
            
            service = LettersService(repo)
            print("\n" + "="*80)
            print("PROBANDO get_letters_to_accept()")
            print("="*80 + "\n")
            
            result = service.get_letters_to_accept()
            
            print(f"\n[RESULTADO] Total de letras retornadas: {len(result)}")
            
            if result:
                print(f"\n[PRIMERA LETRA]")
                print(json.dumps(result[0], indent=2, default=str))
                print(f"\n[CAMPOS DE LA PRIMERA LETRA]")
                for key, value in result[0].items():
                    print(f"  - {key}: {value} (tipo: {type(value).__name__})")
            else:
                print("\n[WARN] No se retornaron letras")
            
            # Probar también la consulta directa
            print("\n" + "="*80)
            print("PROBANDO CONSULTA DIRECTA A ODOO")
            print("="*80 + "\n")
            
            domain = [
                ('state', '=', 'to_accept'),
                ('l10n_latam_boe_number', '!=', False),
                ('l10n_latam_boe_number', '!=', ''),
            ]
            
            move_fields = ['id', 'name', 'state', 'l10n_latam_boe_number']
            moves = repo.search_read('account.move', domain, move_fields, limit=5)
            
            print(f"Letras encontradas directamente: {len(moves)}")
            if moves:
                print("\nPrimeras 3 letras:")
                for i, move in enumerate(moves[:3], 1):
                    print(f"  {i}. ID: {move.get('id')}, Name: {move.get('name')}, State: {move.get('state')}, BOE: {move.get('l10n_latam_boe_number')}")
            
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_endpoint()

