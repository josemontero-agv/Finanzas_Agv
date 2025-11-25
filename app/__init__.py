# -*- coding: utf-8 -*-
"""
Factory de la aplicación Finanzas AGV.

Implementa el patrón Factory para crear instancias de la aplicación Flask
con diferentes configuraciones.
"""

from flask import Flask, jsonify
from flask_caching import Cache
from flask_compress import Compress
from flask_mail import Mail
from config import config

# Inicializar extensiones
cache = Cache()
compress = Compress()
mail = Mail()


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
    
    # Configurar Flask-Caching
    app.config['CACHE_TYPE'] = 'simple'  # 'redis' para producción
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutos
    cache.init_app(app)
    
    # Configurar Flask-Compress
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html',
        'text/css',
        'text/javascript',
        'application/json',
        'application/javascript'
    ]
    app.config['COMPRESS_LEVEL'] = 6
    app.config['COMPRESS_MIN_SIZE'] = 500
    compress.init_app(app)
    
    # Configurar Flask-Mail
    mail.init_app(app)
    
    # Registrar blueprints API
    from app.auth import auth_bp
    from app.collections import collections_bp
    from app.treasury import treasury_bp
    from app.exports import exports_bp
    from app.emails import emails_bp
    from app.letters import letters_bp
    from app.detractions import detractions_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(treasury_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(emails_bp)
    app.register_blueprint(letters_bp)
    app.register_blueprint(detractions_bp)
    
    # Registrar blueprint Web (Frontend)
    from app.web import web_bp
    app.register_blueprint(web_bp)
    
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
                'treasury': '/api/v1/treasury',
                'exports': '/api/v1/exports',
                'emails': '/api/v1/emails',
                'letters': '/api/v1/letters',
                'detractions': '/api/v1/detractions'
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
    print(f"[OK] Blueprints API registrados: auth, collections, treasury, exports, emails, letters, detractions")
    print(f"[OK] Blueprint Web (Frontend) registrado")
    print(f"[OK] Flask-Caching configurado (timeout: 300s)")
    print(f"[OK] Flask-Compress configurado (nivel: 6)")
    print(f"[OK] Flask-Mail configurado (servidor: {app.config.get('MAIL_SERVER', 'N/A')})")
    
    return app
