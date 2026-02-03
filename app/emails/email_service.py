# -*- coding: utf-8 -*-
"""
Servicio de Envío de Emails.
"""

from flask_mail import Mail, Message
from flask import current_app, render_template
from app.emails.email_logger import EmailLogger

class EmailService:
    """
    Servicio para envío de correos electrónicos.
    """
    
    def __init__(self, mail_instance=None):
        """
        Inicializa el servicio de emails.
        """
        if mail_instance:
            self.mail = mail_instance
        else:
            # Obtener instancia de Flask-Mail desde la app
            try:
                self.mail = current_app.extensions.get('mail')
            except RuntimeError:
                # Fuera de contexto de aplicación
                self.mail = None
        
        # Inicializar logger de auditoría
        self.logger = EmailLogger()
    
    def send_letters_to_recover(self, recipients_data):
        """
        Envía correos de letras por recuperar.
        
        Args:
            recipients_data (list): Lista de dict con datos de destinatarios
                [{
                    'email': 'cliente@example.com',
                    'name': 'Cliente',
                    'letters': [...]  # Datos de letras
                }, ...]
        
        Returns:
            dict: Resultado del envío
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for recipient in recipients_data:
            try:
                # Renderizar template
                html_body = render_template(
                    'emails/letters_recover.html',
                    customer_name=recipient['name'],
                    letters=recipient['letters']
                )
                
                # Configurar mensaje
                subject = f"Recordatorio de Firma de Letras - {recipient['name']}"
                
                # Enviar correo
                if self.mail:
                    msg = Message(
                        subject=subject,
                        recipients=[recipient['email']],
                        html=html_body,
                        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@agrovetmarket.com')
                    )
                    self.mail.send(msg)
                    print(f"[OK] Email enviado a {recipient['email']}")
                else:
                    # MOCK SEND: Imprimir en consola si no hay configuración de mail
                    print(f"--- SIMULATING EMAIL SEND TO {recipient['email']} ---")
                    print(f"Subject: {subject}")
                    print("------------------------------------------------")
                
                results['sent'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error enviando a {recipient.get('name', 'Unknown')}: {str(e)}")
        
        return results
    
    def send_letters_in_bank(self, recipients_data):
        """
        Envía correos de letras en banco.
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        for recipient in recipients_data:
            try:
                # Renderizar template
                html_body = render_template(
                    'emails/letters_bank.html',
                    customer_name=recipient['name'],
                    letters=recipient['letters']
                )
                
                # Configurar mensaje
                subject = f"Aviso de Letras Disponibles para Pago - {recipient['name']}"
                
                # Enviar correo
                if self.mail:
                    msg = Message(
                        subject=subject,
                        recipients=[recipient['email']],
                        html=html_body,
                        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@agrovetmarket.com')
                    )
                    self.mail.send(msg)
                    print(f"[OK] Email enviado a {recipient['email']}")
                else:
                    # MOCK SEND
                    print(f"--- SIMULATING EMAIL SEND TO {recipient['email']} ---")
                    print(f"Subject: {subject}")
                    print("------------------------------------------------")
                
                results['sent'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error enviando a {recipient.get('name', 'Unknown')}: {str(e)}")
                
        return results
    
    def send_detraction_certificates(self, recipients_data):
        """
        Envía constancias de detracción de manera masiva.
        """
        raise NotImplementedError("Funcionalidad pendiente de implementación")
    
    def send_acceptance_reminders(self, recipients_data):
        """
        Envía correos para firma de letras (estado 'to_accept').
        
        Args:
            recipients_data (list): Lista de dict con datos de destinatarios
                [{
                    'email': 'cliente@example.com',
                    'name': 'Cliente',
                    'letters': [...]  # Datos de letras
                }, ...]
        
        Returns:
            dict: Resultado del envío
        """
        results = {
            'sent': 0,
            'failed': 0,
            'errors': []
        }
        
        # Verificar si estamos en modo desarrollo
        dev_mode = current_app.config.get('DEV_EMAIL_MODE', False)
        dev_email = current_app.config.get('DEV_EMAIL_RECIPIENT', 'josemontero2415@gmail.com')
        
        for recipient in recipients_data:
            try:
                # Construir lista de letras en HTML
                letters_list_html = "<ul style='list-style-type: none; padding-left: 0;'>"
                for letter in recipient['letters']:
                    letters_list_html += f"""
                    <li style='margin-bottom: 10px; padding: 8px; background-color: #f8f9fa; border-left: 3px solid #714B67;'>
                        <strong>Letra {letter.get('number', 'N/A')}</strong> - 
                        {letter.get('currency', 'PEN')} {letter.get('amount', 0):,.2f} - 
                        Vence: {letter.get('due_date', 'N/A')}
                    </li>
                    """
                letters_list_html += "</ul>"
                
                # Plantilla de correo según especificación del usuario
                body_html = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                    <p>Buenas tardes Estimada/o,</p>
                    <p>Se adjunta las letras para su pronta firma:</p>
                    {letters_list_html}
                    <p>Por favor responder correo cuando se esté enviando las letras firmadas.</p>
                    <br>
                    <p>Cordialmente,<br>
                    <strong>José Montero</strong> | Asistente de Créditos y Cobranzas<br>
                    (1) 2300 300 Anexo | +51 965 252 063 | jose.montero@agrovetmarket.com</p>
                </body>
                </html>
                """
                
                subject = f"Letras Pendientes de Firma - {recipient['name']}"
                
                # Obtener IDs de letras para logging
                letter_ids = [l.get('id') for l in recipient['letters'] if l.get('id')]
                
                # Determinar destinatario real (modo desarrollo o producción)
                original_email = recipient['email']
                actual_recipient = dev_email if dev_mode else original_email
                
                # Agregar nota en el asunto si estamos en modo desarrollo
                if dev_mode:
                    subject = f"[DEV - Original: {original_email}] {subject}"
                
                # Enviar correo
                if self.mail:
                    msg = Message(
                        subject=subject,
                        recipients=[actual_recipient],
                        html=body_html,
                        sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'jose.montero@agrovetmarket.com')
                    )
                    self.mail.send(msg)
                    
                    if dev_mode:
                        print(f"[DEV MODE] Email redirigido de {original_email} a {actual_recipient}")
                    else:
                        print(f"[OK] Email de aceptación enviado a {original_email}")
                    
                    # Log exitoso
                    self.logger.log_email_sent(
                        recipient_email=original_email,
                        recipient_name=recipient['name'],
                        subject=subject,
                        letter_count=len(recipient['letters']),
                        letter_ids=letter_ids
                    )
                else:
                    # MOCK SEND (para desarrollo sin configuración SMTP)
                    print(f"--- SIMULATING EMAIL SEND TO {actual_recipient} ---")
                    if dev_mode:
                        print(f"[DEV MODE] Original destinatario: {original_email}")
                    print(f"Subject: {subject}")
                    print("------------------------------------------------")
                    
                    # Log como enviado incluso en modo mock
                    self.logger.log_email_sent(
                        recipient_email=original_email,
                        recipient_name=recipient['name'],
                        subject=subject,
                        letter_count=len(recipient['letters']),
                        letter_ids=letter_ids
                    )
                
                results['sent'] += 1
                
            except Exception as e:
                results['failed'] += 1
                error_msg = f"Error enviando a {recipient.get('name', 'Unknown')}: {str(e)}"
                results['errors'].append(error_msg)
                print(f"[ERROR] {error_msg}")
                
                # Log del error
                letter_ids = [l.get('id') for l in recipient.get('letters', []) if l.get('id')]
                self.logger.log_email_failed(
                    recipient_email=recipient.get('email', 'unknown'),
                    recipient_name=recipient.get('name', 'Unknown'),
                    subject=subject,
                    error_message=str(e),
                    letter_ids=letter_ids
                )
                
                import traceback
                traceback.print_exc()
        
        return results
    
    def send_bulk_email(self, recipients, subject, body_html, attachments=None):
        """
        Método genérico para envío masivo de correos.
        """
        raise NotImplementedError("Funcionalidad pendiente de implementación")
