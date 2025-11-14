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


class TestingConfig(Config):
    """Configuración de testing."""
    
    DEBUG = True
    TESTING = True
    
    # Credenciales de prueba (mock)
    ODOO_URL = 'http://localhost:8069'
    ODOO_DB = 'test_db'
    ODOO_USER = 'test_user'
    ODOO_PASSWORD = 'test_password'


# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

