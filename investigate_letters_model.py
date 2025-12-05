# -*- coding: utf-8 -*-
"""
Script para investigar el modelo de letras de cambio en Odoo.
Este script ayuda a identificar los campos correctos del módulo de letras.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.core.odoo import OdooRepository

def investigate_letters_model():
    """Investiga el modelo de letras de cambio en Odoo."""
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
            
            print("=" * 80)
            print("INVESTIGACIÓN DEL MODELO DE LETRAS DE CAMBIO")
            print("=" * 80)
            
            # 1. Obtener todos los campos de account.move
            print("\n[1] Campos disponibles en account.move:")
            print("-" * 80)
            fields_info = None
            try:
                fields_info = repo.execute_kw('account.move', 'fields_get', [], {})
                if fields_info:
                    # Filtrar campos relacionados con letras de cambio
                    boe_fields = {k: v for k, v in fields_info.items() 
                                 if 'boe' in k.lower() or 'letter' in k.lower() or 'bill' in k.lower()}
                    
                    print(f"Total de campos en account.move: {len(fields_info)}")
                    print(f"Campos relacionados con letras: {len(boe_fields)}")
                    print("\nCampos relacionados con letras de cambio:")
                    for field_name, field_info in sorted(boe_fields.items()):
                        field_type = field_info.get('type', 'unknown')
                        field_string = field_info.get('string', '')
                        print(f"  - {field_name}: {field_type} ({field_string})")
                    
                    # Buscar campos de estado
                    state_fields = {k: v for k, v in fields_info.items() 
                                  if 'state' in k.lower() and ('boe' in k.lower() or 'letter' in k.lower())}
                    if state_fields:
                        print("\nCampos de ESTADO relacionados con letras:")
                        for field_name, field_info in state_fields.items():
                            field_type = field_info.get('type', 'unknown')
                            field_string = field_info.get('string', '')
                            selection = field_info.get('selection', [])
                            print(f"  - {field_name}: {field_type} ({field_string})")
                            if selection:
                                print(f"    Valores posibles: {selection}")
                    else:
                        # Buscar todos los campos de estado
                        all_state_fields = {k: v for k, v in fields_info.items() if 'state' in k.lower()}
                        print("\nTodos los campos de estado en account.move:")
                        for field_name, field_info in sorted(all_state_fields.items()):
                            field_type = field_info.get('type', 'unknown')
                            field_string = field_info.get('string', '')
                            selection = field_info.get('selection', [])
                            print(f"  - {field_name}: {field_type} ({field_string})")
                            if selection and len(selection) < 20:  # Solo mostrar si no son demasiados
                                print(f"    Valores: {selection}")
                else:
                    print("No se pudieron obtener los campos")
            except Exception as e:
                print(f"[ERROR] Error obteniendo campos: {e}")
                import traceback
                traceback.print_exc()
            
            # 2. Buscar modelos relacionados con letras
            print("\n[2] Buscando modelos relacionados con letras de cambio:")
            print("-" * 80)
            possible_models = [
                'account.bill.form',
                'account.bill.of.exchange',
                'account.letter',
                'l10n_latam.boe',
                'l10n_latam.bill.of.exchange',
                'agr.bill.form',
                'agr.letter',
                'bill.form',
                'bill.of.exchange',
                'account.bill',
                'account.boe'
            ]
            
            found_models = []
            for model_name in possible_models:
                try:
                    # Intentar obtener campos del modelo
                    fields = repo.execute_kw(model_name, 'fields_get', [], {})
                    if fields:
                        found_models.append(model_name)
                        print(f"\n✓ Modelo encontrado: {model_name}")
                        print(f"  Campos disponibles: {len(fields)}")
                        # Mostrar algunos campos clave
                        key_fields = ['name', 'invoice_ids', 'state', 'partner_id', 'date', 'number']
                        for key_field in key_fields:
                            if key_field in fields:
                                field_info = fields[key_field]
                                field_type = field_info.get('type', 'unknown')
                                field_string = field_info.get('string', '')
                                print(f"  - {key_field}: {field_type} ({field_string})")
                except Exception as e:
                    # Modelo no existe, continuar
                    pass
            
            if not found_models:
                print("No se encontraron modelos específicos de letras de cambio")
                print("(Esto es normal si todo está en account.move)")
            
            # 3. Buscar registros de ejemplo con l10n_latam_boe_number
            print("\n[3] Analizando registros de ejemplo con letras:")
            print("-" * 80)
            try:
                # Buscar facturas con número de letra
                sample_moves = repo.search_read(
                    'account.move',
                    [('l10n_latam_boe_number', '!=', False)],
                    ['id', 'name', 'l10n_latam_boe_number', 'state'],
                    limit=5
                )
                
                if sample_moves:
                    print(f"Encontradas {len(sample_moves)} facturas con letras de ejemplo")
                    # Obtener todos los campos de un registro de ejemplo
                    if sample_moves:
                        example_id = sample_moves[0]['id']
                        print(f"\nAnalizando registro ID {example_id}...")
                        print(f"  - Nombre: {sample_moves[0].get('name', 'N/A')}")
                        print(f"  - Número Letra: {sample_moves[0].get('l10n_latam_boe_number', 'N/A')}")
                        print(f"  - Estado: {sample_moves[0].get('state', 'N/A')}")
                        
                        # Obtener todos los campos disponibles
                        if fields_info:
                            # Filtrar campos relevantes
                            relevant_fields = [f for f in fields_info.keys() 
                                             if any(term in f.lower() for term in ['boe', 'letter', 'bill', 'state', 'accept', 'form'])]
                            
                            if relevant_fields:
                                print(f"\nObteniendo valores de {len(relevant_fields)} campos relevantes...")
                                example_data = repo.read('account.move', [example_id], relevant_fields)
                                if example_data:
                                    print("\nValores de campos relacionados con letras:")
                                    for field, value in sorted(example_data[0].items()):
                                        if value or field.endswith('_id'):  # Mostrar campos con valor o relaciones
                                            if isinstance(value, list) and len(value) > 0:
                                                print(f"  - {field}: {value[0] if len(value) == 1 else value}")
                                            else:
                                                print(f"  - {field}: {value}")
                else:
                    print("No se encontraron facturas con número de letra")
                    print("Intentando buscar cualquier factura para análisis...")
                    # Buscar cualquier factura
                    any_move = repo.search_read(
                        'account.move',
                        [],
                        ['id', 'name', 'state'],
                        limit=1
                    )
                    if any_move:
                        print(f"Ejemplo de factura (ID {any_move[0]['id']}): {any_move[0].get('name', 'N/A')}")
            except Exception as e:
                print(f"[ERROR] Error analizando registros: {e}")
                import traceback
                traceback.print_exc()
            
            # 4. Buscar vistas relacionadas con letras
            print("\n[4] Buscando vistas del módulo de letras:")
            print("-" * 80)
            try:
                # Buscar vistas que contengan 'boe' o 'letter' en el nombre
                views = repo.execute_kw('ir.ui.view', 'search_read', 
                    [[('model', '=', 'account.move'), ('name', 'ilike', 'letter')]],
                    {'fields': ['name', 'type', 'arch'], 'limit': 10})
                
                if views:
                    print(f"Encontradas {len(views)} vistas relacionadas con letras")
                    for view in views:
                        print(f"  - {view.get('name', 'N/A')} ({view.get('type', 'N/A')})")
                else:
                    # Buscar con 'boe'
                    views_boe = repo.execute_kw('ir.ui.view', 'search_read', 
                        [[('model', '=', 'account.move'), ('name', 'ilike', 'boe')]],
                        {'fields': ['name', 'type'], 'limit': 10})
                    if views_boe:
                        print(f"Encontradas {len(views_boe)} vistas relacionadas con BOE")
                        for view in views_boe:
                            print(f"  - {view.get('name', 'N/A')} ({view.get('type', 'N/A')})")
            except Exception as e:
                print(f"[WARN] No se pudieron obtener vistas: {e}")
            
            # 5. Buscar menús y acciones relacionadas con letras
            print("\n[5] Buscando menús y acciones del módulo de letras:")
            print("-" * 80)
            try:
                menus = repo.execute_kw('ir.ui.menu', 'search_read',
                    [[('name', 'ilike', 'letra')]],
                    {'fields': ['name', 'action'], 'limit': 10})
                
                if menus:
                    print(f"Encontrados {len(menus)} menús relacionados con letras:")
                    for menu in menus:
                        print(f"  - {menu.get('name', 'N/A')}")
            except Exception as e:
                print(f"[WARN] No se pudieron obtener menús: {e}")
            
            print("\n" + "=" * 80)
            print("INVESTIGACIÓN COMPLETA")
            print("=" * 80)
            print("\nRECOMENDACIONES:")
            print("1. Revisa los campos de estado encontrados arriba")
            print("2. Verifica qué campo contiene el valor 'to_accept'")
            print("3. Confirma si account.move es el modelo correcto o hay otro")
            print("4. Revisa los valores de ejemplo para entender la estructura")
            
        except Exception as e:
            print(f"[ERROR] Error en la investigación: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    investigate_letters_model()

