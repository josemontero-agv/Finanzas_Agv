# -*- coding: utf-8 -*-
"""
Configuración de la aplicación Finanzas AGV.

Define diferentes configuraciones para desarrollo y producción.
Las credenciales se cargan desde archivos .env específicos.
"""

import os
from dotenv import load_dotenv


class Config:
    """Configuración base."""
    
    # Configuración Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-me')
    JSON_AS_ASCII = False  # Soporte para caracteres UTF-8 en JSON
    JSON_SORT_KEYS = False  # No ordenar las claves en JSON
    
    # Configuración Odoo
    ODOO_URL = os.getenv('ODOO_URL')
    ODOO_DB = os.getenv('ODOO_DB')
    ODOO_USER = os.getenv('ODOO_USER')
    ODOO_PASSWORD = os.getenv('ODOO_PASSWORD')
    
    # Configuración Supabase (PostgreSQL)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    # Connection string para SQLAlchemy/psycopg2
    # Formato: postgresql://user:password@host:port/dbname
    SUPABASE_DB_URI = os.getenv('SUPABASE_DB_URI')
    
    # Configuración Redis & Cache
    # Si no hay REDIS_URL, usa memoria simple (para dev sin docker)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'SimpleCache') # 'RedisCache' en prod
    CACHE_REDIS_URL = REDIS_URL
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Configuración Celery
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Configuración Gmail SMTP
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'jose.montero@agrovetmarket.com')
    
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
        """Carga variables de entorno desde .env.desarrollo."""
        env_path = os.path.join(os.path.dirname(__file__), '.env.desarrollo')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print(f"[INFO] Cargando configuración de desarrollo desde: {env_path}")
        else:
            print(f"[WARN] No se encontró archivo .env.desarrollo en: {env_path}")
        
        # Recargar variables después de load_dotenv
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
        app.config['ODOO_URL'] = os.getenv('ODOO_URL')
        app.config['ODOO_DB'] = os.getenv('ODOO_DB')
        app.config['ODOO_USER'] = os.getenv('ODOO_USER')
        app.config['ODOO_PASSWORD'] = os.getenv('ODOO_PASSWORD')
        
        # Supabase & Redis
        app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
        app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY')
        app.config['SUPABASE_DB_URI'] = os.getenv('SUPABASE_DB_URI')
        app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        app.config['CELERY_BROKER_URL'] = app.config['REDIS_URL']
        app.config['CELERY_RESULT_BACKEND'] = app.config['REDIS_URL']
        
        app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'jose.montero@agrovetmarket.com')

        # Configuración Celery Dict
        app.config['CELERY'] = {
            'broker_url': app.config.get('CELERY_BROKER_URL'),
            'result_backend': app.config.get('CELERY_RESULT_BACKEND'),
            'task_ignore_result': True,
        }


class ProductionConfig(Config):
    """Configuración de producción."""
    
    DEBUG = False
    TESTING = False
    
    @classmethod
    def init_app(cls, app):
        """Carga variables de entorno desde .env.produccion."""
        env_path = os.path.join(os.path.dirname(__file__), '.env.produccion')
        if os.path.exists(env_path):
            load_dotenv(env_path, override=True)
            print(f"[INFO] Cargando configuración de producción desde: {env_path}")
        else:
            print(f"[WARN] No se encontró archivo .env.produccion en: {env_path}")
        
        # Recargar variables después de load_dotenv
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'production-secret-key')
        app.config['ODOO_URL'] = os.getenv('ODOO_URL')
        app.config['ODOO_DB'] = os.getenv('ODOO_DB')
        app.config['ODOO_USER'] = os.getenv('ODOO_USER')
        app.config['ODOO_PASSWORD'] = os.getenv('ODOO_PASSWORD')
        
        # Supabase & Redis
        app.config['SUPABASE_URL'] = os.getenv('SUPABASE_URL')
        app.config['SUPABASE_KEY'] = os.getenv('SUPABASE_KEY')
        app.config['SUPABASE_DB_URI'] = os.getenv('SUPABASE_DB_URI')
        app.config['REDIS_URL'] = os.getenv('REDIS_URL') # En prod debe existir
        app.config['CACHE_TYPE'] = 'RedisCache'
        app.config['CELERY_BROKER_URL'] = app.config['REDIS_URL']
        app.config['CELERY_RESULT_BACKEND'] = app.config['REDIS_URL']
        
        app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
        app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
        app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
        app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
        app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
        app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'jose.montero@agrovetmarket.com')

        # Configuración Celery Dict
        app.config['CELERY'] = {
            'broker_url': app.config.get('CELERY_BROKER_URL'),
            'result_backend': app.config.get('CELERY_RESULT_BACKEND'),
            'task_ignore_result': True,
        }


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
