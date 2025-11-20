# -*- coding: utf-8 -*-
"""
Rutas de Emails.

PLACEHOLDER - Endpoints para envío de correos.
"""

from flask import request, jsonify
from app.emails import emails_bp
from app.emails.email_service import EmailService


@emails_bp.route('/send/letters-to-recover', methods=['POST'])
def send_letters_to_recover():
    """
    Endpoint para enviar correos de letras por recuperar.
    
    Request Body (JSON):
        {
            "recipients": [...],
            "date_from": "2024-01-01",
            "date_to": "2024-12-31"
        }
    
    Response (JSON):
        {
            "success": true,
            "sent": 10,
            "failed": 0
        }
    
    TODO: Implementar lógica completa
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@emails_bp.route('/send/letters-in-bank', methods=['POST'])
def send_letters_in_bank():
    """
    Endpoint para enviar correos de letras en banco.
    
    TODO: Implementar lógica completa
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@emails_bp.route('/send/detraction-certificates', methods=['POST'])
def send_detraction_certificates():
    """
    Endpoint para enviar constancias de detracción masivamente.
    
    TODO: Implementar lógica completa con adjuntos
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@emails_bp.route('/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado del módulo de emails.
    """
    return jsonify({
        'module': 'emails',
        'status': 'active',
        'implementation_status': 'placeholder',
        'endpoints': [
            '/send/letters-to-recover',
            '/send/letters-in-bank',
            '/send/detraction-certificates',
            '/status'
        ],
        'note': 'Módulo en fase de estructura - Implementación pendiente'
    }), 200

