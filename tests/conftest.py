# -*- coding: utf-8 -*-
"""Fixtures compartidas para pytest."""

import pytest

from app import create_app


@pytest.fixture
def app():
    """App Flask en modo testing (sin Odoo/Supabase reales)."""
    return create_app('testing')


@pytest.fixture
def client(app):
    """Cliente de prueba Flask."""
    return app.test_client()
