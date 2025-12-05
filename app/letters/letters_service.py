# -*- coding: utf-8 -*-
"""
Servicio de Letras de Cambio.
"""
from datetime import datetime, timedelta
import random

class LettersService:
    """
    Servicio para gestión de letras de cambio.
    """
    
    def __init__(self, odoo_repository):
        """
        Inicializa el servicio de letras.
        
        Args:
            odoo_repository (OdooRepository): Instancia del repositorio de Odoo
        """
        self.repository = odoo_repository
    
    def get_letters_to_recover(self, start_date=None, end_date=None, customer=None):
        """
        Obtiene letras pendientes de recuperar (MOCK DATA).
        """
        # TODO: Implementar consulta real a Odoo
        
        # Mock data generation
        mock_data = []
        customers = [
            {'name': 'Agrovet S.A.', 'vat': '20123456789', 'city': 'Lima'},
            {'name': 'Distribuidora Norte', 'vat': '20543219876', 'city': 'Trujillo'},
            {'name': 'Farmacia Central', 'vat': '20987654321', 'city': 'Lima'},
            {'name': 'Veterinaria Los Andes', 'vat': '20456789123', 'city': 'Huancayo'},
            {'name': 'Agropecuaria Del Sur', 'vat': '20789123456', 'city': 'Arequipa'}
        ]
        users = ['Juan Perez', 'Maria Garcia', 'Carlos Lopez']
        
        for i in range(1, 25): 
            # Using "date" as Issue Date. 
            # Logic says we need to recover it shortly after issue.
            issue_dt = datetime.now() - timedelta(days=random.randint(1, 20))
            due_dt = issue_dt + timedelta(days=random.randint(30, 90))
            
            cust = random.choice(customers)
            cust_name = cust['name']
            
            # Filtros simples mockeados
            if customer and customer.lower() not in cust_name.lower():
                continue
                
            # Calculate STATUS based on user formula:
            # =SI(K2="Lima"; SI(HOY()-G2>4; "POR RECUPERAR"; "VIGENTE"); SI(HOY()-G2>10; "POR RECUPERAR"; "VIGENTE"))
            # Assuming G2 is Issue Date (date) because tracking signature recovery against due date (future) is unusual.
            # If user insists on Due Date, we can swap 'issue_dt' with 'due_dt' here, but logic results would be weird.
            # Using Issue Date makes "Por Recuperar" mean "Late to be signed".
            
            days_since_issue = (datetime.now() - issue_dt).days
            status_calc = "VIGENTE"
            
            if cust['city'] == 'Lima':
                if days_since_issue > 4:
                    status_calc = "POR RECUPERAR"
            else: # Provincia
                if days_since_issue > 10:
                    status_calc = "POR RECUPERAR"

            mock_data.append({
                'id': i,
                'vat': cust['vat'],
                'acceptor_id': cust_name, # Cliente/Aceptante
                'number': f'L-{2024000+i}', # Nro. Letra
                'ref_docs': f'F001-{random.randint(1000,9999)}', # Planilla/Facturas
                'amount': round(random.uniform(1000, 50000), 2), # Total firmado
                'currency': 'PEN',
                'invoice_origin': f'OP-{random.randint(10000,99999)}', # Origen
                'date': issue_dt.strftime('%Y-%m-%d'), # Fecha Emisión
                'due_date': due_dt.strftime('%Y-%m-%d'), # Fecha Vencimiento
                'status_calc': status_calc, # Estado Calculado
                'salesperson': random.choice(users), # Vendedor
                'city': cust['city'], # Ciudad
                'payment_state': 'no_paid', # Estado Pago
                'ref': f'REF-{i}', # Referencia
                'days_overdue': (datetime.now() - due_dt).days if datetime.now() > due_dt else 0
            })
            
        return mock_data
    
    def get_letters_to_accept(self):
        """
        Obtiene letras en estado 'to_accept' (Por aceptar) con todos los campos necesarios.
        Consulta directamente desde account.move en Odoo.
        
        Returns:
            list: Lista de letras con campos completos para envío de correos
        """
        if not self.repository or not self.repository.is_connected():
            print("[WARN] No hay conexión a Odoo, usando datos mock")
            return self._get_mock_letters_to_accept()
        
        try:
            print("[INFO] Consultando letras desde account.move...")
            
            # Construir dominio para letras en estado 'to_accept' (Por aceptar)
            # Según la investigación: el campo 'state' contiene 'to_accept' para letras por aceptar
            # Primero intentar solo con el estado, luego agregar filtros adicionales
            domain = [
                ('state', '=', 'to_accept'),  # Estado específico del módulo de letras
            ]
            
            # Campos a extraer de account.move
            move_fields = [
                'id', 'name', 'partner_id', 'l10n_latam_boe_number',
                'amount_total_in_currency_signed', 'invoice_origin',
                'invoice_date', 'invoice_date_due', 'state',
                'invoice_user_id', 'ref', 'bill_form_id', 'currency_id',
                'acceptor_id', 'bill_form_invoices'
            ]
            
            # Obtener letras con estado 'to_accept'
            try:
                print(f"[DEBUG] Consultando con dominio: {domain}")
                moves = self.repository.search_read(
                    'account.move', domain, move_fields, limit=1000
                )
                print(f"[OK] Encontradas {len(moves)} letras con estado 'to_accept'")
                
                # Filtrar solo las que tienen número de letra (si es necesario)
                if moves:
                    moves_with_boe = [m for m in moves if m.get('l10n_latam_boe_number')]
                    print(f"[INFO] De {len(moves)} letras, {len(moves_with_boe)} tienen número de letra")
                    if moves_with_boe:
                        moves = moves_with_boe
                    else:
                        print("[WARN] Ninguna letra tiene número de letra, mostrando todas")
            except Exception as e:
                print(f"[ERROR] Error al obtener letras: {e}")
                import traceback
                traceback.print_exc()
                return []
            
            if not moves:
                print("[INFO] No se encontraron letras con estado 'to_accept'")
                # Intentar sin filtro de número de letra para debug
                try:
                    domain_simple = [('state', '=', 'to_accept')]
                    moves_simple = self.repository.search_read(
                        'account.move', domain_simple, ['id', 'name', 'state', 'l10n_latam_boe_number'], limit=5
                    )
                    print(f"[DEBUG] Sin filtro de BOE: {len(moves_simple)} letras encontradas")
                    if moves_simple:
                        print("[DEBUG] Ejemplos:")
                        for m in moves_simple[:3]:
                            print(f"  - ID: {m.get('id')}, Name: {m.get('name')}, State: {m.get('state')}, BOE: {m.get('l10n_latam_boe_number')}")
                except:
                    pass
                return []
            
            # Extraer IDs únicos para relaciones (manejar casos donde pueden ser False o listas vacías)
            partner_ids = []
            user_ids = []
            acceptor_ids = []
            
            for m in moves:
                if m.get('partner_id') and isinstance(m['partner_id'], (list, tuple)) and len(m['partner_id']) > 0:
                    partner_ids.append(m['partner_id'][0])
                if m.get('invoice_user_id') and isinstance(m['invoice_user_id'], (list, tuple)) and len(m['invoice_user_id']) > 0:
                    user_ids.append(m['invoice_user_id'][0])
                if m.get('acceptor_id') and isinstance(m['acceptor_id'], (list, tuple)) and len(m['acceptor_id']) > 0:
                    acceptor_ids.append(m['acceptor_id'][0])
            
            partner_ids = list(set(partner_ids))
            user_ids = list(set(user_ids))
            acceptor_ids = list(set(acceptor_ids))
            
            # Obtener datos de partners (clientes)
            partner_map = {}
            if partner_ids:
                partner_fields = ['id', 'name', 'vat', 'city', 'email']
                partners = self.repository.read('res.partner', partner_ids, partner_fields)
                partner_map = {p['id']: p for p in partners}
            
            # Obtener datos de acceptors (aceptantes) - pueden ser diferentes de partners
            acceptor_map = {}
            if acceptor_ids:
                acceptor_fields = ['id', 'name', 'vat', 'city', 'email']
                acceptors = self.repository.read('res.partner', acceptor_ids, acceptor_fields)
                acceptor_map = {a['id']: a for a in acceptors}
            
            # Obtener datos de usuarios (vendedores)
            user_map = {}
            if user_ids:
                user_fields = ['id', 'name']
                users = self.repository.read('res.users', user_ids, user_fields)
                user_map = {u['id']: u for u in users}
            
            # Obtener facturas relacionadas desde bill_form_id si existe
            bill_form_map = {}
            bill_form_ids = []
            for m in moves:
                if m.get('bill_form_id'):
                    if isinstance(m['bill_form_id'], (list, tuple)) and len(m['bill_form_id']) > 0:
                        bill_form_ids.append(m['bill_form_id'][0])
            
            if bill_form_ids:
                bill_form_ids = list(set(bill_form_ids))
                try:
                    # Intentar leer el modelo de planilla de letras (puede tener diferentes nombres)
                    # Intentamos varios nombres posibles del modelo
                    model_names = ['account.bill.form', 'agr.bill.form', 'bill.form']
                    bill_forms = []
                    
                    for model_name in model_names:
                        try:
                            bill_form_fields = ['id', 'name', 'invoice_ids']
                            bill_forms = self.repository.read(model_name, bill_form_ids, bill_form_fields)
                            print(f"[OK] Modelo encontrado: {model_name}")
                            break
                        except:
                            continue
                    
                    if bill_forms:
                        bill_form_map = {bf['id']: bf for bf in bill_forms}
                        
                        # Obtener nombres de facturas relacionadas
                        for bf in bill_forms:
                            invoice_ids = bf.get('invoice_ids', [])
                            if invoice_ids:
                                try:
                                    related_invoices = self.repository.read('account.move', invoice_ids, ['id', 'name'])
                                    bf['invoice_names'] = [inv.get('name', '') for inv in related_invoices]
                                except:
                                    bf['invoice_names'] = []
                except Exception as e:
                    print(f"[WARN] No se pudo obtener bill_form_id: {e}")
                    bill_form_map = {}
            
            # Extraer nombre de Many2One fields
            def m2o_name(field_value):
                if isinstance(field_value, (list, tuple)) and len(field_value) >= 2:
                    return field_value[1]
                elif isinstance(field_value, (list, tuple)) and len(field_value) >= 1:
                    return str(field_value[0])
                return ''
            
            # Procesar y formatear datos
            letters = []
            for move in moves:
                try:
                    # Extraer IDs de manera segura
                    partner_id = None
                    if move.get('partner_id') and isinstance(move['partner_id'], (list, tuple)) and len(move['partner_id']) > 0:
                        partner_id = move['partner_id'][0]
                    
                    acceptor_id = None
                    if move.get('acceptor_id') and isinstance(move['acceptor_id'], (list, tuple)) and len(move['acceptor_id']) > 0:
                        acceptor_id = move['acceptor_id'][0]
                    
                    user_id = None
                    if move.get('invoice_user_id') and isinstance(move['invoice_user_id'], (list, tuple)) and len(move['invoice_user_id']) > 0:
                        user_id = move['invoice_user_id'][0]
                    
                    # Obtener datos de los mapas
                    partner = partner_map.get(partner_id) if partner_id else None
                    acceptor = acceptor_map.get(acceptor_id) if acceptor_id else None
                    user = user_map.get(user_id) if user_id else None
                    
                    # Usar acceptor si existe, sino usar partner
                    client_data = acceptor if acceptor else partner
                    
                    # Obtener número de factura desde bill_form_id si existe, sino usar name
                    bill_form_id = None
                    if move.get('bill_form_id') and isinstance(move['bill_form_id'], (list, tuple)) and len(move['bill_form_id']) > 0:
                        bill_form_id = move['bill_form_id'][0]
                    invoice_number = move.get('name', '')  # Por defecto usar name de la factura
                    
                    # Intentar obtener desde bill_form_id -> invoice_ids
                    if bill_form_id and bill_form_id in bill_form_map:
                        bill_form = bill_form_map[bill_form_id]
                        invoice_names = bill_form.get('invoice_names', [])
                        if invoice_names:
                            invoice_number = ', '.join(invoice_names)
                    
                    # Si bill_form_invoices tiene un ID directo, obtener esa factura
                    elif move.get('bill_form_invoices'):
                        try:
                            invoice_id = move.get('bill_form_invoices')
                            if isinstance(invoice_id, int):
                                related_invoice = self.repository.read('account.move', [invoice_id], ['name'])
                                if related_invoice:
                                    invoice_number = related_invoice[0].get('name', invoice_number)
                        except:
                            pass
                    
                    # Obtener moneda
                    currency_code = 'PEN'  # Por defecto
                    if move.get('currency_id'):
                        try:
                            currency_id = None
                            if isinstance(move['currency_id'], (list, tuple)) and len(move['currency_id']) > 0:
                                currency_id = move['currency_id'][0]
                            elif isinstance(move['currency_id'], int):
                                currency_id = move['currency_id']
                            
                            if currency_id:
                                currencies = self.repository.read('res.currency', [currency_id], ['name'])
                                if currencies:
                                    currency_code = currencies[0].get('name', 'PEN')
                        except Exception as e:
                            print(f"[WARN] Error obteniendo moneda: {e}")
                            pass
                    
                    # Calcular estado según lógica: Lima >4 días = POR RECUPERAR, Provincia >10 días = POR RECUPERAR
                    invoice_date = move.get('invoice_date')
                    status_calc = "VIGENTE"
                    city = client_data.get('city', '') if client_data else ''
                    
                    if invoice_date:
                        try:
                            from datetime import datetime
                            issue_dt = datetime.strptime(invoice_date, '%Y-%m-%d')
                            days_since_issue = (datetime.now() - issue_dt).days
                            
                            if city == 'Lima':
                                if days_since_issue > 4:
                                    status_calc = "POR RECUPERAR"
                            else:  # Provincia
                                if days_since_issue > 10:
                                    status_calc = "POR RECUPERAR"
                        except:
                            pass
                    
                    letter_data = {
                        'id': move['id'],
                        'vat': client_data.get('vat', '') if client_data else '',  # Ruc
                        'acceptor_id': client_data.get('name', '') if client_data else '',  # Cliente (aceptante)
                        'number': move.get('l10n_latam_boe_number', ''),  # Letra
                        'ref_docs': invoice_number,  # Número (desde bill_form_id/invoice_ids o name)
                        'amount': move.get('amount_total_in_currency_signed', 0.0),  # Monto
                        'currency': currency_code,  # Moneda extraída de currency_id
                        'invoice_origin': move.get('invoice_origin', ''),  # Planilla Interna
                        'date': move.get('invoice_date', ''),  # F. Emision
                        'due_date': move.get('invoice_date_due', ''),  # F. Vencimiento
                        'status_calc': status_calc,  # Estado calculado
                        'salesperson': m2o_name(move.get('invoice_user_id')),  # Vendedor
                        'city': city,  # Ciudad
                        'customer_email': client_data.get('email', '') if client_data else '',
                        'customer_name': client_data.get('name', '') if client_data else '',
                        'ref': move.get('ref', ''),
                        'state': move.get('state', '')
                    }
                    
                    letters.append(letter_data)
                except Exception as e:
                    print(f"[ERROR] Error procesando letra ID {move.get('id', 'N/A')}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"[OK] Procesadas {len(letters)} letras")
            return letters
            
        except Exception as e:
            print(f"[ERROR] Error consultando letras desde Odoo: {e}")
            import traceback
            traceback.print_exc()
            # Fallback a mock data en caso de error
            return self._get_mock_letters_to_accept()
    
    def _get_mock_letters_to_accept(self):
        """Genera datos mock para letras to_accept."""
        
        mock_data = []
        customers = [
            {'name': 'Agrovet S.A.', 'vat': '20123456789', 'city': 'Lima', 'email': 'josemontero2415@gmail.com'},
            {'name': 'Distribuidora Norte', 'vat': '20543219876', 'city': 'Trujillo', 'email': 'josemontero2415@gmail.com'},
            {'name': 'Farmacia Central', 'vat': '20987654321', 'city': 'Lima', 'email': 'josemontero2415@gmail.com'},
            {'name': 'Veterinaria Los Andes', 'vat': '20456789123', 'city': 'Huancayo', 'email': 'josemontero2415@gmail.com'},
            {'name': 'Agropecuaria Del Sur', 'vat': '20789123456', 'city': 'Arequipa', 'email': 'josemontero2415@gmail.com'}
        ]
        users = ['Juan Perez', 'Maria Garcia', 'Carlos Lopez']
        
        for i in range(1, 15):
            issue_dt = datetime.now() - timedelta(days=random.randint(1, 20))
            due_dt = issue_dt + timedelta(days=random.randint(30, 90))
            
            cust = random.choice(customers)
            
            # Calcular estado
            days_since_issue = (datetime.now() - issue_dt).days
            status_calc = "VIGENTE"
            
            if cust['city'] == 'Lima':
                if days_since_issue > 4:
                    status_calc = "POR RECUPERAR"
            else:
                if days_since_issue > 10:
                    status_calc = "POR RECUPERAR"
            
            mock_data.append({
                'id': i,
                'vat': cust['vat'],
                'acceptor_id': cust['name'],
                'number': f'L-{2024000+i}',
                'ref_docs': f'F001-{random.randint(1000,9999)}, F002-{random.randint(1000,9999)}',
                'amount': round(random.uniform(1000, 50000), 2),
                'currency': 'PEN',
                'invoice_origin': f'OP-{random.randint(10000,99999)}',
                'date': issue_dt.strftime('%Y-%m-%d'),
                'due_date': due_dt.strftime('%Y-%m-%d'),
                'status_calc': status_calc,
                'salesperson': random.choice(users),
                'city': cust['city'],
                'customer_email': cust['email'],
                'customer_name': cust['name'],
                'ref': f'REF-{i}'
            })
        
        return mock_data
    
    def get_letters_in_bank(self, start_date=None, end_date=None, bank=None):
        """
        Obtiene letras que están en el banco (MOCK DATA).
        """
        # Mock data generation
        mock_data = []
        customers = ['Agrovet S.A.', 'Distribuidora Norte', 'Farmacia Central', 'Veterinaria Los Andes']
        banks = ['BBVA', 'BCP', 'INTERBANK']
        
        for i in range(100, 130): 
            due_dt = datetime.now() + timedelta(days=random.randint(1, 60))
            bank_name = random.choice(banks)
            
            if bank and bank.lower() != bank_name.lower():
                continue
                
            mock_data.append({
                'id': i,
                'number': f'L-{2024000+i}',
                'payment_number': f'{random.randint(1000000, 9999999)}',
                'customer': random.choice(customers),
                'bank': bank_name,
                'amount': round(random.uniform(1000, 50000), 2),
                'currency': 'USD' if random.random() > 0.5 else 'PEN',
                'due_date': due_dt.strftime('%Y-%m-%d'),
                'status': 'En Banco'
            })
            
        return mock_data
    
    def generate_bank_schedule(self, letter_ids, bank_format='standard'):
        """
        Genera planilla de letras para envío al banco.
        """
        raise NotImplementedError("Funcionalidad pendiente de implementación")
    
    def get_letters_summary(self, group_by='customer'):
        """
        Obtiene resumen de letras para el dashboard (MOCK DATA).
        """
        to_recover = self.get_letters_to_recover()
        in_bank = self.get_letters_in_bank()
        
        # KPIs
        total_recover_amount = sum(l['amount'] for l in to_recover) 
        total_bank_amount = sum(l['amount'] for l in in_bank) 
        
        # Chart 1: Ageing of Letters to Recover
        # Using days_overdue might be 0 if we used Issue Date logic above, 
        # but let's keep tracking overdue against due_date for the chart if needed,
        # OR track "Days since Issue" for the recovery chart.
        # Let's use "Days since Issue" for the chart to align with "Recovery".
        
        ageing = {'0-4': 0, '5-10': 0, '11-30': 0, '>30': 0}
        for l in to_recover:
            # Calculate days since issue
            issue_date = datetime.strptime(l['date'], '%Y-%m-%d')
            days = (datetime.now() - issue_date).days
            
            if days <= 4: ageing['0-4'] += 1
            elif days <= 10: ageing['5-10'] += 1
            elif days <= 30: ageing['11-30'] += 1
            else: ageing['>30'] += 1
            
        # Chart 2: Letters in Bank by Bank
        by_bank = {}
        for l in in_bank:
            b = l['bank']
            by_bank[b] = by_bank.get(b, 0) + l['amount']
            
        return {
            'kpi': {
                'to_recover': {
                    'count': len(to_recover),
                    'amount': total_recover_amount
                },
                'in_bank': {
                    'count': len(in_bank),
                    'amount': total_bank_amount
                }
            },
            'charts': {
                'ageing': list(ageing.values()),
                'ageing_labels': list(ageing.keys()),
                'by_bank': [{'name': k, 'value': v} for k, v in by_bank.items()]
            }
        }
