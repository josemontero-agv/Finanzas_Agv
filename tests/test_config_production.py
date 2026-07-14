# -*- coding: utf-8 -*-
"""Smoke tests de validación de configuración en producción."""

from unittest.mock import MagicMock, patch

import pytest

from app import create_app
from config import Config, ProductionConfig


def _make_app_config(**overrides):
    base = {
        'SECRET_KEY': 'secure-random-production-secret-key-32',
        'JWT_SECRET_KEY': 'secure-random-jwt-secret-key-32chars',
        'ALLOWED_USERS': ['user@example.com'],
        'COLLECTIONS_SOURCE': 'odoo',
        'SUPABASE_DB_URI': None,
    }
    base.update(overrides)
    app = MagicMock()
    app.config = base
    return app


class TestProductionConfigValidation:
    """Valida reglas de seguridad de ProductionConfig._validate_production_config."""

    @pytest.mark.parametrize('insecure_secret', sorted(Config.INSECURE_SECRET_VALUES))
    def test_rejects_insecure_secret_key(self, insecure_secret):
        app = _make_app_config(SECRET_KEY=insecure_secret)
        with pytest.raises(RuntimeError, match='SECRET_KEY'):
            ProductionConfig._validate_production_config(app)

    @pytest.mark.parametrize('insecure_secret', sorted(Config.INSECURE_SECRET_VALUES))
    def test_rejects_insecure_jwt_secret_key(self, insecure_secret):
        app = _make_app_config(JWT_SECRET_KEY=insecure_secret)
        with pytest.raises(RuntimeError, match='JWT_SECRET_KEY'):
            ProductionConfig._validate_production_config(app)

    def test_rejects_empty_secret_key(self):
        app = _make_app_config(SECRET_KEY='')
        with pytest.raises(RuntimeError, match='SECRET_KEY'):
            ProductionConfig._validate_production_config(app)

    def test_rejects_empty_allowed_users(self):
        app = _make_app_config(ALLOWED_USERS=[])
        with pytest.raises(RuntimeError, match='ALLOWED_USERS'):
            ProductionConfig._validate_production_config(app)

    def test_accepts_valid_config(self):
        app = _make_app_config()
        ProductionConfig._validate_production_config(app)

    def test_warns_supabase_without_db_uri(self):
        app = _make_app_config(COLLECTIONS_SOURCE='supabase', SUPABASE_DB_URI=None)
        with pytest.warns(UserWarning, match='SUPABASE_DB_URI'):
            ProductionConfig._validate_production_config(app)

    def test_no_warning_supabase_with_db_uri(self):
        import warnings

        app = _make_app_config(
            COLLECTIONS_SOURCE='supabase',
            SUPABASE_DB_URI='postgresql://user:pass@host:6543/db',
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            ProductionConfig._validate_production_config(app)
        assert len(caught) == 0


class TestCreateAppProduction:
    """Integración: create_app('production') aplica validación tras cargar env."""

    @patch('config.load_dotenv')
    def test_create_app_production_rejects_default_secrets(self, _mock_load_dotenv, monkeypatch):
        monkeypatch.delenv('SECRET_KEY', raising=False)
        monkeypatch.delenv('JWT_SECRET_KEY', raising=False)
        monkeypatch.delenv('ALLOWED_USERS', raising=False)

        with pytest.raises(RuntimeError, match='SECRET_KEY'):
            create_app('production')

    @patch('config.load_dotenv')
    def test_create_app_production_accepts_valid_env(self, _mock_load_dotenv, monkeypatch):
        monkeypatch.setenv('SECRET_KEY', 'ci-production-secret-key-32chars-min')
        monkeypatch.setenv('JWT_SECRET_KEY', 'ci-jwt-production-secret-32chars')
        monkeypatch.setenv('ALLOWED_USERS', 'test@agrovetmarket.com')

        app = create_app('production')
        assert app.config['SECRET_KEY'] == 'ci-production-secret-key-32chars-min'
        assert app.config['ALLOWED_USERS'] == ['test@agrovetmarket.com']
