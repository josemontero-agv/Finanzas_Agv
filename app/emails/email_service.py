# -*- coding: utf-8 -*-
"""
Servicio de Envío de Emails.
"""

from pathlib import Path
from flask_mail import Mail, Message
from flask import current_app
from jinja2 import Environment, FileSystemLoader
from app.emails.email_logger import EmailLogger
from datetime import datetime, timedelta
import re

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

    def _is_valid_email(self, value):
        """
        Valida formato básico de email para evitar rechazos SMTP por destinatarios inválidos.
        """
        if not value:
            return False
        return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value))

    def _split_emails(self, raw_value):
        """
        Convierte un string o lista de correos en lista normalizada/única de emails válidos.
        Acepta separadores coma y punto y coma.
        """
        if not raw_value:
            return []

        if isinstance(raw_value, (list, tuple)):
            candidates = raw_value
        else:
            normalized = str(raw_value).strip().strip('"').strip("'").replace(';', ',')
            candidates = normalized.split(',')

        result = []
        seen = set()
        for item in candidates:
            email = str(item).strip().strip('"').strip("'").lower()
            if not email or not self._is_valid_email(email):
                continue
            if email in seen:
                continue
            seen.add(email)
            result.append(email)
        return result

    def _get_config_emails(self, key):
        """
        Obtiene lista de correos desde config (MAIL_DEFAULT_CC / MAIL_DEFAULT_BCC, etc).
        """
        return self._split_emails(current_app.config.get(key, ''))

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

    def _is_lima(self, city):
        """
        Determina si la ciudad corresponde a Lima.
        """
        city_value = (city or "").strip().lower()
        return city_value == "lima" or city_value.startswith("lima ")
    
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
        default_cc = self._get_config_emails('MAIL_DEFAULT_CC')
        default_bcc = self._get_config_emails('MAIL_DEFAULT_BCC')
        
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
                                # Fecha límite para cliente: Lima +7 días, provincia +15 días
                                deadline_days = 7 if self._is_lima(l.get('city', '')) else 15
                                limit_date = date_obj.date() + timedelta(days=deadline_days)
                                letter_copy['limit_date'] = limit_date.strftime('%d/%m/%Y')
                                letter_copy['is_limit_overdue'] = datetime.now().date() > limit_date
                        except:
                            pass

                    if 'limit_date' not in letter_copy:
                        letter_copy['limit_date'] = '-'
                    if 'is_limit_overdue' not in letter_copy:
                        letter_copy['is_limit_overdue'] = False
                    
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
                customer_recipients = self._split_emails(original_email)
                dev_recipients = self._split_emails(dev_email)
                to_recipients = dev_recipients if dev_mode else customer_recipients

                if not to_recipients:
                    results['failed'] += 1
                    error_msg = (
                        f"Error enviando a {recipient.get('name', 'Unknown')}: "
                        "No hay destinatarios válidos para envío"
                    )
                    results['errors'].append(error_msg)
                    print(f"[ERROR] {error_msg}")
                    self.logger.log_email_failed(
                        recipient_email=original_email or 'unknown',
                        recipient_name=recipient.get('name', 'Unknown'),
                        subject=subject,
                        error_message="No hay destinatarios válidos para envío",
                        letter_ids=letter_ids
                    )
                    continue

                # Si el cliente tiene múltiples correos, el primero va en TO y el resto en CC.
                # Además, se agregan CC/BCC de configuración.
                customer_cc = [] if dev_mode else customer_recipients[1:]
                cc_recipients = []
                bcc_recipients = []
                for email in customer_cc + default_cc:
                    if email not in to_recipients and email not in cc_recipients:
                        cc_recipients.append(email)
                for email in default_bcc:
                    if email not in to_recipients and email not in cc_recipients and email not in bcc_recipients:
                        bcc_recipients.append(email)
                
                # Agregar nota en el asunto si estamos en modo desarrollo
                if dev_mode:
                    subject = f"[DEV - Original: {original_email}] {subject}"
                
                # Enviar correo
                if self.mail:
                    resolved_sender = self._resolve_sender_email(sender_email)
                    msg = Message(
                        subject=subject,
                        recipients=to_recipients,
                        cc=cc_recipients,
                        bcc=bcc_recipients,
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
                        print(f"[DEV MODE] Email redirigido de {original_email} a {', '.join(to_recipients)}")
                    else:
                        print(
                            f"[OK] Email de aceptación enviado a TO={','.join(to_recipients)}"
                            + (f" CC={','.join(cc_recipients)}" if cc_recipients else "")
                            + (f" BCC={','.join(bcc_recipients)}" if bcc_recipients else "")
                        )
                    
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
                    print(f"--- SIMULATING EMAIL SEND TO {', '.join(to_recipients)} ---")
                    if dev_mode:
                        print(f"[DEV MODE] Original destinatario: {original_email}")
                    if cc_recipients:
                        print(f"CC: {', '.join(cc_recipients)}")
                    if bcc_recipients:
                        print(f"BCC: {', '.join(bcc_recipients)}")
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
