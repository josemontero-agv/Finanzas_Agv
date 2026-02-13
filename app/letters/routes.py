# -*- coding: utf-8 -*-
"""
Rutas de Letras de Cambio.

Endpoints para gestión de letras y envío de correos.
"""

from flask import request, jsonify, current_app
from app.letters import letters_bp
from app.letters.letters_service import LettersService
from app.emails.email_service import EmailService
from app.core.odoo import OdooRepository
from app.auth.security import require_login, get_authenticated_user_email

def get_odoo_repository():
    """Helper para crear instancia de OdooRepository desde la configuración."""
    try:
        return OdooRepository(
            url=current_app.config.get('ODOO_URL'),
            db=current_app.config.get('ODOO_DB'),
            username=current_app.config.get('ODOO_USER'),
            password=current_app.config.get('ODOO_PASSWORD')
        )
    except Exception as e:
        print(f"[WARN] No se pudo crear OdooRepository: {e}")
        return None

def get_letters_service():
    """Helper para obtener instancia de LettersService con repositorio."""
    repo = get_odoo_repository()
    return LettersService(odoo_repository=repo)

def get_email_service():
    """Helper para obtener instancia de EmailService."""
    return EmailService()


@letters_bp.route('/to-accept', methods=['GET'])
@require_login
def get_letters_to_accept():
    """
    Endpoint para obtener letras en estado 'to_accept' (Por aceptar).
    
    Returns:
        JSON con letras pendientes de aceptación
    """
    try:
        print("[INFO] Endpoint /to-accept llamado")
        service = get_letters_service()
        print("[INFO] Servicio obtenido, llamando get_letters_to_accept()...")
        data = service.get_letters_to_accept()
        print(f"[INFO] Servicio retornó {len(data) if data else 0} letras")
        
        response_data = {
            'success': True,
            'data': data if data else [],
            'count': len(data) if data else 0
        }
        
        print(f"[INFO] Enviando respuesta con {response_data['count']} letras")
        return jsonify(response_data)
    except Exception as e:
        print(f"[ERROR] Error en get_letters_to_accept: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e),
            'data': [],
            'count': 0
        }), 500


@letters_bp.route('/to-recover', methods=['GET'])
@require_login
def get_letters_to_recover():
    """
    Endpoint para obtener letras por recuperar.
    
    Query Parameters:
        - start_date (opt): Fecha inicial YYYY-MM-DD
        - end_date (opt): Fecha final YYYY-MM-DD
        - customer (opt): Nombre parcial del cliente
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        customer = request.args.get('customer')
        
        service = get_letters_service()
        data = service.get_letters_to_recover(start_date, end_date, customer)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@letters_bp.route('/in-bank', methods=['GET'])
@require_login
def get_letters_in_bank():
    """
    Endpoint para obtener letras en banco.
    
    Query Parameters:
        - start_date (opt): Fecha inicial YYYY-MM-DD
        - end_date (opt): Fecha final YYYY-MM-DD
        - bank (opt): Nombre del banco
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        bank = request.args.get('bank')
        
        service = get_letters_service()
        data = service.get_letters_in_bank(start_date, end_date, bank)
        
        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@letters_bp.route('/send-acceptance', methods=['POST'])
@require_login
def send_acceptance_emails():
    """
    Envía correos de recordatorio de firma para letras en estado 'to_accept'.
    
    Body: { "letter_ids": ["id1", "id2"] }
    """
    try:
        data = request.get_json()
        # Aceptar tanto letter_ids como letterIds (compatibilidad)
        letter_ids = data.get('letter_ids', data.get('letterIds', []))
        
        if not letter_ids:
            return jsonify({'success': False, 'message': 'No se seleccionaron letras'}), 400
        
        # 1. Obtener detalles solo de las letras seleccionadas
        service = get_letters_service()
        selected_letters = service.get_letters_to_accept(letter_ids=letter_ids)
        
        if not selected_letters:
            return jsonify({'success': False, 'message': 'No se encontraron las letras seleccionadas en el sistema'}), 404
        
        # 2. Agrupar por email del cliente (puede haber múltiples letras por cliente)
        dev_mode = current_app.config.get('DEV_EMAIL_MODE', False)
        dev_recipient = current_app.config.get('DEV_EMAIL_RECIPIENT', '')
        grouped_by_email = {}
        skipped_letters = []

        for letter in selected_letters:
            email = letter.get('customer_email', '')
            customer_name = letter.get('customer_name', letter.get('acceptor_id', 'Cliente'))

            # En modo desarrollo, enviar todo al destinatario de prueba
            if dev_mode and dev_recipient:
                email = dev_recipient
            
            if not email:
                skipped_letters.append({
                    'id': letter.get('id'),
                    'number': letter.get('number', 'N/A'),
                    'acceptor_id': letter.get('acceptor_id', ''),
                    'reason': 'Sin email de cliente'
                })
                print(f"[WARN] Letra {letter.get('number', 'N/A')} no tiene email de cliente, se omite")
                continue
            
            if email not in grouped_by_email:
                grouped_by_email[email] = {
                    'name': customer_name,
                    'email': email,
                    'letters': []
                }
            grouped_by_email[email]['letters'].append(letter)
        
        if not grouped_by_email:
            return jsonify({
                'success': False,
                'message': 'Ninguna letra seleccionada tiene email de cliente',
                'skipped': skipped_letters
            }), 400
        
        # 3. Enviar correos usando el método de aceptación
        email_service = get_email_service()
        recipients_data = list(grouped_by_email.values())
        sender_email = get_authenticated_user_email()
        result = email_service.send_acceptance_reminders(
            recipients_data,
            sender_email=sender_email
        )
        
        return jsonify({
            'success': True,
            'message': 'Proceso de envío completado',
            'details': result,
            'skipped': skipped_letters,
            'dev_mode': dev_mode,
            'dev_recipient': dev_recipient if dev_mode else None
        })
        
    except Exception as e:
        print(f"Error en send_acceptance_emails: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Error interno: {str(e)}"
        }), 500


@letters_bp.route('/send-recover', methods=['POST'])
@require_login
def send_recover_emails():
    """
    Envía correos de recordatorio de firma.
    
    Body: { "letter_ids": ["id1", "id2"] }
    """
    try:
        data = request.get_json()
        # Aceptar tanto letter_ids como letterIds (compatibilidad)
        letter_ids = data.get('letter_ids', data.get('letterIds', []))
        
        if not letter_ids:
            return jsonify({'success': False, 'message': 'No se seleccionaron letras'}), 400
        
        # 1. Obtener detalles completos de las letras
        service = get_letters_service()
        all_letters = service.get_letters_to_recover()
        
        # Convertir IDs a strings para comparación segura
        letter_ids_str = [str(lid) for lid in letter_ids]
        selected_letters = [l for l in all_letters if str(l['id']) in letter_ids_str]
        
        if not selected_letters:
            return jsonify({'success': False, 'message': 'No se encontraron letras seleccionadas'}), 404
        grouped_by_customer = {}
        for letter in selected_letters:
            # Usamos nombre del cliente como key temporal. Idealmente usar ID cliente o Email.
            # Simulamos email basado en nombre
            customer_name = letter.get('acceptor_id', 'Cliente')
            email = f"contacto@{customer_name.lower().replace(' ', '').replace('.', '')}.com"
            
            if customer_name not in grouped_by_customer:
                grouped_by_customer[customer_name] = {
                    'name': customer_name,
                    'email': email,
                    'letters': []
                }
            grouped_by_customer[customer_name]['letters'].append(letter)
        
        # 3. Enviar correos
        email_service = get_email_service()
        recipients_data = list(grouped_by_customer.values())
        sender_email = get_authenticated_user_email()
        result = email_service.send_letters_to_recover(
            recipients_data,
            sender_email=sender_email
        )
        
        return jsonify({
            'success': True,
            'message': 'Proceso de envío completado',
            'details': result
        })
        
    except Exception as e:
        print(f"Error en send_recover_emails: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error interno: {str(e)}"
        }), 500


@letters_bp.route('/send-bank', methods=['POST'])
@require_login
def send_bank_emails():
    """
    Envía avisos de letras en banco (Número de pago).
    
    Body: { "letter_ids": ["id1", "id2"] }
    """
    try:
        data = request.get_json()
        # Aceptar tanto letter_ids como letterIds (compatibilidad)
        letter_ids = data.get('letter_ids', data.get('letterIds', []))
        
        if not letter_ids:
            return jsonify({'success': False, 'message': 'No se seleccionaron letras'}), 400
            
        # 1. Obtener detalles
        service = get_letters_service()
        all_letters = service.get_letters_in_bank()
        
        # Convertir IDs a strings para comparación segura
        letter_ids_str = [str(lid) for lid in letter_ids]
        selected_letters = [l for l in all_letters if str(l['id']) in letter_ids_str]
        
        if not selected_letters:
            return jsonify({'success': False, 'message': 'No se encontraron letras seleccionadas'}), 404
        grouped_by_customer = {}
        for letter in selected_letters:
            customer_name = letter['customer']
            email = f"pagos@{customer_name.lower().replace(' ', '').replace('.', '')}.com"
            
            if customer_name not in grouped_by_customer:
                grouped_by_customer[customer_name] = {
                    'name': customer_name,
                    'email': email,
                    'letters': []
                }
            grouped_by_customer[customer_name]['letters'].append(letter)
            
        # 3. Enviar correos
        email_service = get_email_service()
        recipients_data = list(grouped_by_customer.values())
        sender_email = get_authenticated_user_email()
        result = email_service.send_letters_in_bank(
            recipients_data,
            sender_email=sender_email
        )
        
        return jsonify({
            'success': True,
            'message': 'Proceso de envío completado',
            'details': result
        })

    except Exception as e:
        print(f"Error en send_bank_emails: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error interno: {str(e)}"
        }), 500


@letters_bp.route('/generate-schedule', methods=['POST'])
@require_login
def generate_bank_schedule():
    """
    Endpoint para generar planilla bancaria de letras.
    TODO: Implementar
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@letters_bp.route('/summary', methods=['GET'])
@require_login
def get_summary():
    """
    Endpoint para obtener resumen de letras.
    """
    try:
        service = get_letters_service()
        summary = service.get_letters_summary()
        return jsonify({
            'success': True,
            'data': summary
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@letters_bp.route('/status', methods=['GET'])
def status():
    """Endpoint para verificar el estado del módulo de letras."""
    return jsonify({
        'module': 'letters',
        'status': 'active',
        'endpoints': [
            '/to-accept',
            '/to-recover',
            '/in-bank',
            '/send-acceptance',
            '/send-recover',
            '/send-bank'
        ]
    }), 200
