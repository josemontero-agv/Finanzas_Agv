# -*- coding: utf-8 -*-
"""
Factory de la aplicación Finanzas AGV.

Implementa el patrón Factory para crear instancias de la aplicación Flask
con diferentes configuraciones.
"""

from urllib.parse import urlsplit
from flask import Flask, jsonify, request
from flask_caching import Cache
from flask_compress import Compress
from flask_mail import Mail
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from config import config
from app.core.celery_utils import celery_init_app

# Inicializar extensiones
cache = Cache()
compress = Compress()
mail = Mail()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
oauth = OAuth()


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
    app.config.setdefault('RESTRICT_TO_LETTERS_ONLY', True)
    
    # Configurar CORS para Next.js frontend
    # localhost:5000 es la propia API, no debe estar como origen permitido
    cors_origins = ["http://localhost:3000"]
    frontend_url = (app.config.get('FRONTEND_URL') or '').strip()
    if frontend_url:
        parsed_frontend = urlsplit(frontend_url)
        if parsed_frontend.scheme and parsed_frontend.netloc:
            frontend_origin = f"{parsed_frontend.scheme}://{parsed_frontend.netloc}"
            if frontend_origin not in cors_origins:
                cors_origins.append(frontend_origin)

    CORS(app, resources={
        r"/api/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Inicializar Celery
    celery_init_app(app)

    # Importar tareas de Celery para que sean registradas
    with app.app_context():
        try:
            from app import tasks
        except ImportError:
            pass
    
    # Configurar Flask-Caching
    # Si está configurado Redis en producción, usarlo
    if app.config.get('CACHE_TYPE') == 'RedisCache':
        app.config['CACHE_REDIS_URL'] = app.config.get('REDIS_URL')
    else:
        app.config['CACHE_TYPE'] = 'simple'
        
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

    # Inicializar Flask-JWT-Extended
    jwt.init_app(app)

    # Inicializar Flask-Limiter
    # storage_uri: usa Redis si está disponible, memoria simple si no
    redis_url = app.config.get('REDIS_URL')
    limiter.storage_uri = redis_url if redis_url else 'memory://'
    limiter.init_app(app)

    # Inicializar cliente OAuth (login con Google)
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )

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

    @app.after_request
    def add_security_headers(response):
        """Añade cabeceras de seguridad a todas las respuestas."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        # HSTS solo en producción (requiere HTTPS activo)
        if not app.debug:
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains'
            )
        return response

    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Respuesta JSON cuando se supera el rate limit."""
        return jsonify({
            'success': False,
            'message': 'Demasiados intentos. Intente nuevamente en unos minutos.',
            'status': 429
        }), 429

    @app.before_request
    def check_csrf():
        """
        Proteccion CSRF basica para endpoints de API.
        - Si el request viene con cabecera Origin, debe ser un origen permitido por CORS.
        - Los requests POST/PUT/PATCH con body deben enviar Content-Type: application/json.
        El frontend (axios con withCredentials) ya cumple ambas condiciones de forma nativa.
        """
        if request.method == 'OPTIONS':
            return None
        if not request.path.startswith('/api/v1/'):
            return None

        origin = request.headers.get('Origin')
        if origin and origin not in cors_origins:
            return jsonify({
                'success': False,
                'message': 'Origen no permitido'
            }), 403

        if request.method in ('POST', 'PUT', 'PATCH') and request.content_length:
            content_type = (request.content_type or '').split(';')[0].strip()
            if content_type and content_type != 'application/json':
                return jsonify({
                    'success': False,
                    'message': 'Content-Type debe ser application/json'
                }), 415

        return None

    @app.before_request
    def restrict_api_modules():
        """
        Restringe temporalmente la API a endpoints de Letras.
        Evita exposición de módulos en desarrollo por acceso directo.
        """
        if not app.config.get('RESTRICT_TO_LETTERS_ONLY', False):
            return None

        if request.method == 'OPTIONS':
            return None

        path = request.path or ''

        # Endpoints públicos fuera de /api/v1
        if path == '/api/health':
            return None

        # Solo controlar endpoints versionados de API
        if not path.startswith('/api/v1/'):
            return None

        allowed_prefixes = (
            '/api/v1/letters',
            '/api/v1/collections',
            '/api/v1/exports/collections',
            '/api/v1/auth/login',
            '/api/v1/auth/logout',
            '/api/v1/auth/status',
            '/api/v1/auth/user-info',
            '/api/v1/auth/google',
        )

        if any(path == prefix or path.startswith(f'{prefix}/') for prefix in allowed_prefixes):
            return None

        return jsonify({
            'success': False,
            'message': 'Módulo no disponible actualmente',
            'status': 403
        }), 403
    
    # Ruta raíz informativa
    @app.route('/')
    def index():
        """Endpoint raíz con información de la API."""
        restricted_mode = app.config.get('RESTRICT_TO_LETTERS_ONLY', False)
        return jsonify({
            'app': 'Finanzas AGV API',
            'version': '1.0.0',
            'description': 'API REST para gestión financiera - Modo Letras + Cobranzas',
            'endpoints': (
                {
                    'auth': '/api/v1/auth',
                    'letters': '/api/v1/letters',
                    'collections': '/api/v1/collections'
                } if restricted_mode else {
                    'auth': '/api/v1/auth',
                    'collections': '/api/v1/collections',
                    'treasury': '/api/v1/treasury',
                    'exports': '/api/v1/exports',
                    'emails': '/api/v1/emails',
                    'letters': '/api/v1/letters',
                    'detractions': '/api/v1/detractions'
                }
            ),
            'restricted_mode': restricted_mode,
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
    print(f"[OK] Restricción temporal de módulos activa: {app.config.get('RESTRICT_TO_LETTERS_ONLY', False)}")
    print(f"[OK] Blueprint Web (Frontend) registrado")
    print(f"[OK] Flask-Caching configurado (timeout: 300s)")
    print(f"[OK] Flask-Compress configurado (nivel: 6)")
    print(f"[OK] Flask-Mail configurado (servidor: {app.config.get('MAIL_SERVER', 'N/A')})")
    print(f"[OK] Flask-JWT-Extended inicializado")
    print(f"[OK] Flask-Limiter inicializado (storage: {'Redis' if redis_url else 'memoria'})")
    print(f"[OK] Security headers habilitados")
    
    return app
