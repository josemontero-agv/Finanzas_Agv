# -*- coding: utf-8 -*-
"""
Rutas de Autenticación.

Endpoints para login y autenticación de usuarios.
"""

from flask import request, jsonify, current_app, session
from app.auth import auth_bp
from app.core.odoo import OdooRepository


def _normalize_user_email(username, provided_email=None):
    """
    Normaliza email corporativo del usuario autenticado.
    Si el username ya es email, lo usa; de lo contrario agrega el dominio corporativo.
    """
    domain = current_app.config.get('USER_EMAIL_DOMAIN', 'agrovetmarket.com').strip().lower()
    candidate = (provided_email or username or '').strip().lower()

    if '@' in candidate:
        return candidate
    if candidate:
        return f'{candidate}@{domain}'
    return ''


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint de login de usuarios.
    
    Autentica un usuario contra Odoo y devuelve un token.
    
    Request Body (JSON):
        {
            "username": "usuario",
            "password": "contraseña"
        }
    
    Response (JSON):
        Success:
            {
                "success": true,
                "message": "Login exitoso",
                "token": "dummy_token_12345",
                "user": "usuario"
            }
        
        Error:
            {
                "success": false,
                "message": "Credenciales inválidas"
            }
    """
    try:
        # Obtener datos del request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Debe enviar datos en formato JSON'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Validar que se enviaron ambos campos
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Se requieren username y password'
            }), 400
        
        # Intentar autenticar contra Odoo
        try:
            odoo_repo = OdooRepository(
                url=current_app.config['ODOO_URL'],
                db=current_app.config['ODOO_DB'],
                username=current_app.config['ODOO_USER'],
                password=current_app.config['ODOO_PASSWORD']
            )
            
            # Autenticar usuario
            if odoo_repo.authenticate_user(username, password):
                user_email = _normalize_user_email(username, data.get('email'))
                session['logged_in'] = True
                session['username'] = username
                session['email'] = user_email
                session.permanent = True

                return jsonify({
                    'success': True,
                    'message': 'Login exitoso',
                    'token': 'dummy_token_12345',  # En producción: generar JWT real
                    'user': username,
                    'email': user_email
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Credenciales inválidas'
                }), 401
                
        except ValueError as ve:
            return jsonify({
                'success': False,
                'message': f'Error de configuración: {str(ve)}'
            }), 500
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error al conectar con Odoo: {str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error interno: {str(e)}'
        }), 500


@auth_bp.route('/user-info', methods=['GET'])
def user_info():
    """
    Endpoint para obtener información del usuario actual desde la sesión.
    
    Response (JSON):
        {
            "success": true,
            "username": "usuario",
            "email": "usuario@agrovet.com.pe"
        }
    """
    if session.get('logged_in'):
        return jsonify({
            'success': True,
            'username': session.get('username', ''),
            'email': session.get('email', '')
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Usuario no autenticado'
        }), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Cierra la sesión del usuario autenticado."""
    session.clear()
    return jsonify({
        'success': True,
        'message': 'Sesión cerrada'
    }), 200


@auth_bp.route('/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado del módulo de autenticación.
    
    Response (JSON):
        {
            "module": "auth",
            "status": "active",
            "endpoints": ["/login", "/status"]
        }
    """
    return jsonify({
        'module': 'auth',
        'status': 'active',
        'endpoints': ['/login', '/logout', '/status', '/user-info']
    }), 200

