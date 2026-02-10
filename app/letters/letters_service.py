# -*- coding: utf-8 -*-
"""
Servicio de Letras de Cambio.
"""
from datetime import datetime, timedelta
import random

class LettersService:
    """
    Servicio para gestión de letras de cambio con integración a Odoo.
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
        Obtiene letras pendientes de recuperar.
        """
        # Nota: Por ahora mantiene lógica mock para esta sección específica
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
            issue_dt = datetime.now() - timedelta(days=random.randint(1, 20))
            due_dt = issue_dt + timedelta(days=random.randint(30, 90))
            cust = random.choice(customers)
            if customer and customer.lower() not in cust['name'].lower():
                continue
                
            status_calc = self._calculate_status(issue_dt.strftime('%Y-%m-%d'), cust['city'])

            mock_data.append({
                'id': i,
                'vat': cust['vat'],
                'acceptor_id': cust['name'],
                'number': f'L-{2024000+i}',
                'ref_docs': f'F001-{random.randint(1000,9999)}',
                'amount': round(random.uniform(1000, 50000), 2),
                'currency': 'PEN',
                'invoice_origin': f'OP-{random.randint(10000,99999)}',
                'date': issue_dt.strftime('%Y-%m-%d'),
                'due_date': due_dt.strftime('%Y-%m-%d'),
                'status_calc': status_calc,
                'salesperson': random.choice(users),
                'city': cust['city'],
                'payment_state': 'no_paid',
                'ref': f'REF-{i}',
                'days_overdue': (datetime.now() - due_dt).days if datetime.now() > due_dt else 0
            })
        return mock_data
    
    def get_letters_to_accept(self, letter_ids=None):
        """
        Obtiene letras en estado 'to_accept' (Por aceptar) con OPTIMIZACIÓN POR LOTES (Batch Mode).
        Trae fecha y vendedor de la FACTURA ORIGINAL navegando entre modelos.
        
        Args:
            letter_ids (list, optional): Lista de IDs específicos a consultar.
        """
        if not self.repository or not self.repository.is_connected():
            print("[WARN] No hay conexión a Odoo, usando datos mock")
            return self._get_mock_letters_to_accept()
        
        try:
            print(f"[INFO] Iniciando consulta optimizada de letras ({'Filtered' if letter_ids else 'All'})...")
            
            # 1. Obtener las letras pendientes (Consulta Única)
            domain = [('move_type', '=', 'out_bill')]
            if letter_ids:
                # Convertir a int si vienen como strings
                ids = [int(lid) for lid in letter_ids]
                domain.append(('id', 'in', ids))
            else:
                domain.append(('state', '=', 'to_accept'))

            move_fields = [
                'id', 'name', 'partner_id', 'l10n_latam_boe_number',
                'amount_total_in_currency_signed', 'invoice_origin',
                'invoice_date', 'invoice_date_due', 'state', 'move_type',
                'invoice_user_id', 'ref', 'bill_form_id', 'currency_id',
                'acceptor_id'
            ]
            moves = self.repository.search_read('account.move', domain, move_fields, limit=1000)
            if not moves:
                print("[INFO] No se encontraron letras con estado 'to_accept'")
                return []

            # 2. Recolectar IDs para consultas en bloque
            partner_ids = set()
            bill_form_ids = set()
            for m in moves:
                if m.get('partner_id'): partner_ids.add(m['partner_id'][0])
                if m.get('acceptor_id'): partner_ids.add(m['acceptor_id'][0])
                if m.get('bill_form_id'): bill_form_ids.add(m['bill_form_id'][0])

            # 3. Consultar Partners y Planillas en bloque (Reduce latencia de red)
            partner_map = {}
            if partner_ids:
                partners = self.repository.read('res.partner', list(partner_ids), ['id', 'name', 'vat', 'city', 'email'])
                partner_map = {p['id']: p for p in partners}

            bill_form_map = {}
            if bill_form_ids:
                bill_forms = self.repository.read('account.bill.form', list(bill_form_ids), ['id', 'invoice_ids'])
                bill_form_map = {bf['id']: bf for bf in bill_forms}

            # 4. Obtener todos los IDs de facturas originales de todas las planillas
            all_invoice_ids = []
            for bf_id, bf_data in bill_form_map.items():
                all_invoice_ids.extend(bf_data.get('invoice_ids', []))
            
            # 5. Consultar detalles de Facturas Originales (Vendedor y Fecha Real)
            invoice_details_map = {}
            if all_invoice_ids:
                invoices = self.repository.read('account.move', list(set(all_invoice_ids)), ['id', 'name', 'invoice_date', 'invoice_user_id'])
                for inv in invoices:
                    invoice_details_map[inv['id']] = {
                        'name': inv.get('name', ''),
                        'date': inv.get('invoice_date'),
                        'user': inv.get('invoice_user_id')[1] if isinstance(inv.get('invoice_user_id'), (list, tuple)) else ''
                    }

            # 6. Reconstrucción de datos en memoria (Velocidad ms)
            letters = []
            for move in moves:
                try:
                    # Identificar cliente (prioridad aceptante)
                    p_id = move.get('acceptor_id')[0] if move.get('acceptor_id') else (move.get('partner_id')[0] if move.get('partner_id') else None)
                    client = partner_map.get(p_id) if p_id else None
                    
                    # Datos base (de la letra)
                    orig_date = move.get('invoice_date')
                    orig_user = move.get('invoice_user_id')[1] if isinstance(move.get('invoice_user_id'), (list, tuple)) else ''
                    # Por defecto usamos la referencia de la letra si no hay planilla
                    orig_invoice_name = move.get('name', '')

                    # Cruzar con factura original si existe planilla (bill_form_id/invoice_ids/name)
                    b_id = move.get('bill_form_id')
                    if b_id and b_id[0] in bill_form_map:
                        inv_ids = bill_form_map[b_id[0]].get('invoice_ids', [])
                        if inv_ids:
                            # Extraer nombres de todas las facturas asociadas a la planilla
                            names = []
                            for iid in inv_ids:
                                if iid in invoice_details_map:
                                    inv_det = invoice_details_map[iid]
                                    names.append(inv_det['name'])
                                    # Usamos la fecha y usuario de la primera factura como referencia
                                    if len(names) == 1:
                                        orig_date = inv_det['date']
                                        orig_user = inv_det['user']
                            
                            if names:
                                orig_invoice_name = ", ".join(names)

                    letters.append({
                        'id': move['id'],
                        'vat': client.get('vat', '') if client else '',
                        'acceptor_id': client.get('name', '') if client else '',
                        'number': move.get('l10n_latam_boe_number', ''),
                        'ref_docs': orig_invoice_name,
                        'amount': move.get('amount_total_in_currency_signed', 0.0),
                        'currency': move.get('currency_id')[1] if move.get('currency_id') else 'PEN',
                        'invoice_date': orig_date,
                        'due_date': move.get('invoice_date_due', ''),
                        'status_calc': self._calculate_status(orig_date, client.get('city', '') if client else ''),
                        'salesperson': orig_user,
                        'customer_email': client.get('email', '') if client else '',
                        'state': move.get('state', '')
                    })
                except Exception as row_error:
                    print(f"[WARN] Error procesando letra {move.get('id')}: {row_error}")
                    continue
            
            print(f"[OK] {len(letters)} letras procesadas con optimización Batch.")
            return letters
        except Exception as e:
            print(f"[ERROR] Error general en get_letters_to_accept: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _calculate_status(self, date_str, city):
        """
        Calcula el estado de la letra según días transcurridos y ciudad.
        
        Reglas:
        - Límite de días: 4 para Lima, 10 para otras ciudades.
        - "VENCIDO"     : days > limit
        - "POR VENCER"  : (limit - 2) < days <= limit
        - "VIGENTE"     : resto de casos o ante errores/fecha vacía.
        """
        if not date_str:
            return "VIGENTE"
        try:
            from datetime import datetime
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            days = (datetime.now() - dt).days
            limit = 4 if city == 'Lima' else 10

            if days > limit:
                return "VENCIDO"
            if days > (limit - 2):
                return "POR VENCER"
            return "VIGENTE"
        except Exception:
            return "VIGENTE"

    def get_letters_in_bank(self, start_date=None, end_date=None, bank=None):
        """
        Obtiene letras enviadas al banco.
        """
        # Mock data por ahora
        return []

    def get_letters_summary(self):
        """
        Obtiene resumen estadístico de letras.
        """
        return {
            'to_accept': 0,
            'to_recover': 0,
            'in_bank': 0
        }

    def _get_mock_letters_to_accept(self):
        """Genera datos mock para pruebas cuando no hay conexión."""
        mock_data = []
        customers = [
            {'name': 'Agrovet S.A.', 'vat': '20123456789', 'city': 'Lima', 'email': 'josemontero2415@gmail.com'},
            {'name': 'Distribuidora Norte', 'vat': '20543219876', 'city': 'Trujillo', 'email': 'josemontero2415@gmail.com'},
            {'name': 'Farmacia Central', 'vat': '20987654321', 'city': 'Lima', 'email': 'josemontero2415@gmail.com'}
        ]
        for i in range(1, 15):
            dt = datetime.now() - timedelta(days=random.randint(1, 15))
            cust = random.choice(customers)
            mock_data.append({
                'id': i,
                'vat': cust['vat'],
                'acceptor_id': cust['name'],
                'number': f'L-MOCK-{i}',
                'ref_docs': f'F001-{100+i}',
                'amount': 1500.0 * i,
                'currency': 'PEN',
                'invoice_date': dt.strftime('%Y-%m-%d'),
                'due_date': (dt + timedelta(days=30)).strftime('%Y-%m-%d'),
                'status_calc': self._calculate_status(dt.strftime('%Y-%m-%d'), cust['city']),
                'salesperson': 'Vendedor Mock',
                'customer_email': cust['email'],
                'state': 'to_accept'
            })
        return mock_data
