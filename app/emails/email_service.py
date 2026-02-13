# -*- coding: utf-8 -*-
"""
Servicio de Envío de Emails.
"""

from pathlib import Path
from flask_mail import Mail, Message
from flask import current_app
from jinja2 import Environment, FileSystemLoader
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

    def _resolve_sender_email(self, sender_email=None):
        """
        Resuelve remitente permitido por dominio corporativo.
        Si no cumple política, usa remitente por defecto configurado.
        """
        default_sender = current_app.config.get('MAIL_DEFAULT_SENDER', 'noreply@agrovetmarket.com')
        allowed_domain = current_app.config.get('ALLOWED_EMAIL_SENDER_DOMAIN', 'agrovetmarket.com').strip().lower()

        candidate = (sender_email or '').strip().lower()
        if candidate and candidate.endswith(f'@{allowed_domain}'):
            return candidate
        return default_sender

    def _get_frontend_templates_dir(self):
        """
        Retorna la ruta absoluta del directorio de templates de email en frontend.
        """
        project_root = Path(current_app.root_path).parent
        return project_root / 'frontend' / 'email-templates'

    def _render_email_template(self, template_name, **context):
        """
        Renderiza un template Jinja2 desde frontend/email-templates.
        """
        templates_dir = self._get_frontend_templates_dir()
        env = Environment(loader=FileSystemLoader(str(templates_dir)))
        template = env.get_template(template_name)
        return template.render(**context)
    
    def send_letters_to_recover(self, recipients_data, sender_email=None):
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
                # Renderizar template (ubicado en frontend/email-templates)
                html_body = self._render_email_template(
                    'letters_recover.html',
                    customer_name=recipient['name'],
                    letters=recipient['letters']
                )
                
                # Configurar mensaje
                subject = f"Recordatorio de Firma de Letras - {recipient['name']}"
                
                # Enviar correo
                if self.mail:
                    resolved_sender = self._resolve_sender_email(sender_email)
                    msg = Message(
                        subject=subject,
                        recipients=[recipient['email']],
                        html=html_body,
                        sender=resolved_sender,
                        reply_to=resolved_sender
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
    
    def send_letters_in_bank(self, recipients_data, sender_email=None):
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
                # Renderizar template (ubicado en frontend/email-templates)
                html_body = self._render_email_template(
                    'letters_bank.html',
                    customer_name=recipient['name'],
                    letters=recipient['letters']
                )
                
                # Configurar mensaje
                subject = f"Aviso de Letras Disponibles para Pago - {recipient['name']}"
                
                # Enviar correo
                if self.mail:
                    resolved_sender = self._resolve_sender_email(sender_email)
                    msg = Message(
                        subject=subject,
                        recipients=[recipient['email']],
                        html=html_body,
                        sender=resolved_sender,
                        reply_to=resolved_sender
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
    
    def send_acceptance_reminders(self, recipients_data, sender_email=None):
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
        dev_email = current_app.config.get('DEV_EMAIL_RECIPIENT', 'creditosycobranzas@agrovetmarket.com')
        
        from datetime import datetime
        now = datetime.now()
        # Formato 3/2/2026 para el cuerpo y 03/02/26 para el asunto
        today_str = f"{now.day}/{now.month}/{now.year}"
        subject_date = now.strftime("%d/%m/%y")

        for recipient in recipients_data:
            try:
                # Formatear fechas para el reporte
                formatted_letters = []
                for l in recipient['letters']:
                    # Clonar y formatear fecha de vencimiento y factura
                    letter_copy = l.copy()
                    if l.get('due_date'):
                        try:
                            date_obj = datetime.strptime(l['due_date'], '%Y-%m-%d')
                            letter_copy['due_date'] = date_obj.strftime('%d/%m/%Y')
                        except:
                            pass
                    
                    if l.get('invoice_date'):
                        try:
                            # Odoo a veces envía datetime o string YYYY-MM-DD
                            inv_date = l['invoice_date']
                            if isinstance(inv_date, str):
                                date_obj = datetime.strptime(inv_date, '%Y-%m-%d')
                                letter_copy['invoice_date'] = date_obj.strftime('%d/%m/%Y')
                        except:
                            pass
                    
                    formatted_letters.append(letter_copy)

                # Renderizar template profesional desde frontend/email-templates
                body_html = self._render_email_template(
                    'letters_acceptance.html',
                    customer_name=recipient['name'],
                    letters=formatted_letters,
                    today=today_str
                )
                
                subject = f"Letras Pendientes de Firma - {recipient['name']} al día {subject_date}"
                
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
                    resolved_sender = self._resolve_sender_email(sender_email)
                    msg = Message(
                        subject=subject,
                        recipients=[actual_recipient],
                        html=body_html,
                        sender=resolved_sender,
                        reply_to=resolved_sender
                    )
                    
                    # Adjuntar logo como CID para que se muestre inline
                    try:
                        import os
                        logo_path = os.path.join(current_app.root_path, '..', 'frontend', 'public', 'img', 'agrovet-market.png')
                        if os.path.exists(logo_path):
                            with open(logo_path, 'rb') as f:
                                msg.attach(
                                    "agrovet-market.png",
                                    "image/png",
                                    f.read(),
                                    'inline',
                                    headers=[['Content-ID', '<logo_agrovet>']]
                                )
                    except Exception as img_err:
                        print(f"[WARN] No se pudo adjuntar el logo: {img_err}")

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
