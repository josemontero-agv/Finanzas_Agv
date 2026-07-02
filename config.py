# -*- coding: utf-8 -*-
"""
Configuración de la aplicación Finanzas AGV.

Define diferentes configuraciones para desarrollo y producción.
Las credenciales se cargan desde archivos .env específicos.
"""

import os
from datetime import timedelta
from dotenv import load_dotenv


class Config:
    """Configuración base."""
    
    # Configuración Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-me')
    JSON_AS_ASCII = False  # Soporte para caracteres UTF-8 en JSON
    JSON_SORT_KEYS = False  # No ordenar las claves en JSON

    # JWT (Flask-JWT-Extended)
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or os.getenv('SECRET_KEY', 'default-secret-key-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    
    # Configuración Odoo
    ODOO_URL = os.getenv('ODOO_URL')
    ODOO_DB = os.getenv('ODOO_DB')
    ODOO_USER = os.getenv('ODOO_USER')
    ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')

    # Login con Google OAuth2
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    ALLOWED_USERS = [
        email.strip().lower()
        for email in os.getenv('ALLOWED_USERS', '').split(',')
        if email.strip()
    ]
    
    # Configuración Supabase (PostgreSQL)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    # Connection string para SQLAlchemy/psycopg2
    # Formato: postgresql://user:password@host:port/dbname
    SUPABASE_DB_URI = os.getenv('SUPABASE_DB_URI')
    
    # Configuración Redis & Cache
    # Si no hay REDIS_URL, usa memoria simple (para dev sin docker)
    REDIS_URL = os.getenv('REDIS_URL')
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple') 
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configuración Celery
    CELERY_BROKER_URL = REDIS_URL if REDIS_URL else 'memory://'
    CELERY_RESULT_BACKEND = REDIS_URL if REDIS_URL else 'memory://'
    
    # Configuración Gmail SMTP
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'jose.montero@agrovetmarket.com')
    MAIL_DEFAULT_CC = os.getenv('MAIL_DEFAULT_CC', '')
    MAIL_DEFAULT_BCC = os.getenv('MAIL_DEFAULT_BCC', '')
    
    # Modo de desarrollo para correos (redirige todos los correos a un email de prueba)
    DEV_EMAIL_MODE = os.getenv('DEV_EMAIL_MODE', 'False').lower() == 'true'
    DEV_EMAIL_RECIPIENT = os.getenv('DEV_EMAIL_RECIPIENT', 'creditosycobranzas@agrovetmarket.com')

    # RBAC: True = solo loggear accesos (no bloquear). Cambiar a False cuando roles estén configurados.
    RBAC_LOG_ONLY = True

    # URL pública del frontend Next.js (para redirecciones del gateway web)
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    # Dominio corporativo para identidad de usuario/remitente
    USER_EMAIL_DOMAIN = os.getenv('USER_EMAIL_DOMAIN', 'agrovetmarket.com')
    ALLOWED_EMAIL_SENDER_DOMAIN = os.getenv('ALLOWED_EMAIL_SENDER_DOMAIN', 'agrovetmarket.com')

    # Sesión y cookies (cross-site)
    SESSION_COOKIE_NAME = os.getenv('SESSION_COOKIE_NAME', 'finanzas_agv_session')
    SESSION_COOKIE_HTTPONLY = os.getenv('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
    SESSION_REFRESH_EACH_REQUEST = os.getenv('SESSION_REFRESH_EACH_REQUEST', 'True').lower() == 'true'
    SESSION_LIFETIME_MINUTES = int(os.getenv('SESSION_LIFETIME_MINUTES', '480'))

    @staticmethod
    def _as_bool(value, default=False):
        if value is None:
            return default
        return str(value).strip().lower() in ('1', 'true', 'yes', 'on')

    @classmethod
    def _apply_session_settings(cls, app, secure_default=False, samesite_default='Lax'):
        """
        Aplica configuración de sesión/cookies con soporte cross-site.
        """
        app.config['SESSION_COOKIE_NAME'] = os.getenv('SESSION_COOKIE_NAME', 'finanzas_agv_session')
        app.config['SESSION_COOKIE_HTTPONLY'] = cls._as_bool(
            os.getenv('SESSION_COOKIE_HTTPONLY'),
            default=True
        )
        app.config['SESSION_COOKIE_SECURE'] = cls._as_bool(
            os.getenv('SESSION_COOKIE_SECURE'),
            default=secure_default
        )

        cookie_samesite = os.getenv('SESSION_COOKIE_SAMESITE', samesite_default)
        if str(cookie_samesite).lower() == 'none':
            cookie_samesite = 'None'
        app.config['SESSION_COOKIE_SAMESITE'] = cookie_samesite

        app.config['SESSION_REFRESH_EACH_REQUEST'] = cls._as_bool(
            os.getenv('SESSION_REFRESH_EACH_REQUEST'),
            default=True
        )
        lifetime_minutes = int(os.getenv('SESSION_LIFETIME_MINUTES', '480'))
        app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=lifetime_minutes)
    
    @classmethod
    def _load_common_env(cls, app, default_secret, dev_email_default):
        """
        Carga variables de entorno comunes a todos los entornos tras load_dotenv.

        Args:
            app: instancia Flask.
            default_secret (str): valor por defecto para SECRET_KEY.
            dev_email_default (str): valor por defecto para DEV_EMAIL_MODE ('True'/'False').
        """
        secret_key = os.getenv('SECRET_KEY', default_secret)
        app.config['SECRET_KEY'] = secret_key
        app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY') or secret_key
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)

        app.config['ODOO_URL'] = os.getenv('ODOO_URL')
        app.config['ODOO_DB'] = os.getenv('ODOO_DB')
        app.config['ODOO_USER'] = os.getenv('ODOO_USER')
        app.config['ODOO_PASSWORD'] = os.getenv('ODOO_PASSWORD')

        app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
        app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
        app.config['ALLOWED_USERS'] = [
            email.strip().lower()
            for email in os.getenv('ALLOWED_USERS', '').split(',')
            if email.strip()
        ]

        app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
        app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY')
        app.config['SUPABASE_DB_URI'] = os.getenv('SUPABASE_DB_URI')

        app.config['REDIS_URL'] = os.getenv('REDIS_URL')
        if app.config['REDIS_URL']:
            app.config['CACHE_TYPE'] = 'RedisCache'
            app.config['CELERY_BROKER_URL'] = app.config['REDIS_URL']
            app.config['CELERY_RESULT_BACKEND'] = app.config['REDIS_URL']
        else:
            app.config['CACHE_TYPE'] = 'simple'
            app.config['CELERY_BROKER_URL'] = 'memory://'
            app.config['CELERY_RESULT_BACKEND'] = 'memory://'

        app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'jose.montero@agrovetmarket.com')
        app.config['MAIL_DEFAULT_CC'] = os.getenv('MAIL_DEFAULT_CC', '')
        app.config['MAIL_DEFAULT_BCC'] = os.getenv('MAIL_DEFAULT_BCC', '')

        app.config['FRONTEND_URL'] = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        app.config['USER_EMAIL_DOMAIN'] = os.getenv('USER_EMAIL_DOMAIN', 'agrovetmarket.com')
        app.config['ALLOWED_EMAIL_SENDER_DOMAIN'] = os.getenv('ALLOWED_EMAIL_SENDER_DOMAIN', 'agrovetmarket.com')

        app.config['DEV_EMAIL_MODE'] = os.getenv('DEV_EMAIL_MODE', dev_email_default).lower() == 'true'
        app.config['DEV_EMAIL_RECIPIENT'] = os.getenv('DEV_EMAIL_RECIPIENT', 'creditosycobranzas@agrovetmarket.com')

        app.config['CELERY'] = {
            'broker_url': app.config.get('CELERY_BROKER_URL'),
            'result_backend': app.config.get('CELERY_RESULT_BACKEND'),
            'task_ignore_result': True,
        }

    @staticmethod
    def init_app(app):
        """Inicialización adicional de la app."""
        pass


class DevelopmentConfig(Config):
    """Configuración de desarrollo."""

    DEBUG = True
    TESTING = False

    @classmethod
    def init_app(cls, app):
        """Carga variables de entorno desde .env.desarrollo y .env.supabase.desarrollo."""
        base_path = os.path.dirname(__file__)
        for env_path in [
            os.path.join(base_path, '.env.desarrollo'),
            os.path.join(base_path, '.env.supabase.desarrollo'),
        ]:
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
                print(f"[INFO] Cargando configuración desde: {env_path}")
            else:
                print(f"[WARN] No se encontró archivo: {env_path}")

        cls._load_common_env(app, default_secret='dev-secret-key', dev_email_default='True')
        cls._apply_session_settings(app, secure_default=False, samesite_default='Lax')


class ProductionConfig(Config):
    """Configuración de producción."""

    DEBUG = False
    TESTING = False

    @classmethod
    def init_app(cls, app):
        """Carga variables de entorno desde .env.produccion y .env.supabase.produccion."""
        base_path = os.path.dirname(__file__)
        for env_path in [
            os.path.join(base_path, '.env.produccion'),
            os.path.join(base_path, '.env.supabase.produccion'),
        ]:
            if os.path.exists(env_path):
                load_dotenv(env_path, override=True)
                print(f"[INFO] Cargando configuración desde: {env_path}")
            else:
                print(f"[WARN] No se encontró archivo: {env_path}")

        cls._load_common_env(app, default_secret='production-secret-key', dev_email_default='False')
        cls._apply_session_settings(app, secure_default=True, samesite_default='None')


class TestingConfig(Config):
    """Configuración de testing."""
    
    DEBUG = True
    TESTING = True
    
    # Credenciales de prueba (mock)
    ODOO_URL = 'http://localhost:8069'
    ODOO_DB = 'test_db'
    ODOO_USER = 'test_user'
    ODOO_PASSWORD = 'test_password'
    
    # Mocks para tests
    REDIS_URL = 'memory://'
    CELERY_BROKER_URL = 'memory://'
    
    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        app.config['CELERY'] = {
            'broker_url': cls.CELERY_BROKER_URL,
            'result_backend': cls.CELERY_BROKER_URL,
            'task_ignore_result': True,
        }


# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
