# -*- coding: utf-8 -*-
"""
Rutas de Letras de Cambio.

PLACEHOLDER - Endpoints para gestión de letras.
"""

from flask import request, jsonify
from app.letters import letters_bp
from app.letters.letters_service import LettersService


@letters_bp.route('/to-recover', methods=['GET'])
def get_letters_to_recover():
    """
    Endpoint para obtener letras por recuperar.
    
    Query Parameters:
        - date_from, date_to, customer
    
    Response (JSON):
        {
            "success": true,
            "data": [...],
            "count": 10
        }
    
    TODO: Implementar lógica completa
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@letters_bp.route('/in-bank', methods=['GET'])
def get_letters_in_bank():
    """
    Endpoint para obtener letras en banco.
    
    TODO: Implementar lógica completa
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@letters_bp.route('/generate-schedule', methods=['POST'])
def generate_bank_schedule():
    """
    Endpoint para generar planilla bancaria de letras.
    
    Request Body (JSON):
        {
            "letter_ids": [1, 2, 3],
            "bank_format": "bbva"
        }
    
    Response:
        Archivo Excel descargable
    
    TODO: Implementar generación de planilla
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@letters_bp.route('/summary', methods=['GET'])
def get_summary():
    """
    Endpoint para obtener resumen de letras.
    
    TODO: Implementar resumen para dashboard
    """
    return jsonify({
        'success': False,
        'message': 'Funcionalidad pendiente de implementación',
        'status': 'not_implemented'
    }), 501


@letters_bp.route('/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado del módulo de letras.
    """
    return jsonify({
        'module': 'letters',
        'status': 'active',
        'implementation_status': 'placeholder',
        'endpoints': [
            '/to-recover',
            '/in-bank',
            '/generate-schedule',
            '/summary',
            '/status'
        ],
        'note': 'Módulo en fase de estructura - Implementación pendiente'
    }), 200

