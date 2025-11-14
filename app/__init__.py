# -*- coding: utf-8 -*-
"""
Factory de la aplicación Finanzas AGV.

Implementa el patrón Factory para crear instancias de la aplicación Flask
con diferentes configuraciones.
"""

from flask import Flask, jsonify
from config import config


def create_app(config_name='development'):
    """
    Factory para crear la aplicación Flask.
    
    Args:
        config_name (str): Nombre de la configuración a usar.
            Opciones: 'development', 'production', 'testing'
    
    Returns:
        Flask: Instancia configurada de la aplicación.
    """
    # Crear instancia de Flask
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Registrar blueprints
    from app.auth import auth_bp
    from app.collections import collections_bp
    from app.treasury import treasury_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(treasury_bp)
    
    # Ruta raíz informativa
    @app.route('/')
    def index():
        """Endpoint raíz con información de la API."""
        return jsonify({
            'app': 'Finanzas AGV API',
            'version': '1.0.0',
            'description': 'API REST para gestión financiera - Cobranzas y Tesorería',
            'endpoints': {
                'auth': '/api/v1/auth',
                'collections': '/api/v1/collections',
                'treasury': '/api/v1/treasury'
            },
            'status': 'running'
        })
    
    # Manejador de errores 404
    @app.errorhandler(404)
    def not_found(error):
        """Manejador de error 404."""
        return jsonify({
            'error': 'Not Found',
            'message': 'El endpoint solicitado no existe',
            'status': 404
        }), 404
    
    # Manejador de errores 500
    @app.errorhandler(500)
    def internal_error(error):
        """Manejador de error 500."""
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Ocurrió un error interno en el servidor',
            'status': 500
        }), 500
    
    print(f"[OK] Aplicación creada con configuración: {config_name}")
    print(f"[OK] Blueprints registrados: auth, collections, treasury")
    
    return app
