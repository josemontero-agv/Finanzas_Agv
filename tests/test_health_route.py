# -*- coding: utf-8 -*-
"""Smoke tests del endpoint /api/health (sin Odoo/Supabase reales)."""

from unittest.mock import MagicMock, patch


def test_health_returns_200_with_services(client):
    with patch('app.web.routes.OdooRepository') as mock_odoo_cls, \
         patch('app.web.routes.SupabaseClient') as mock_supabase:
        mock_odoo_cls.return_value.is_connected.return_value = True
        mock_supabase.get_client.return_value = MagicMock()

        response = client.get('/api/health')

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['version'] == '2.0.0'
    assert data['services']['odoo'] == 'connected'
    assert data['services']['supabase'] == 'connected'


def test_health_odoo_disconnected_still_healthy(client):
    with patch('app.web.routes.OdooRepository') as mock_odoo_cls, \
         patch('app.web.routes.SupabaseClient') as mock_supabase:
        mock_odoo_cls.return_value.is_connected.return_value = False
        mock_supabase.get_client.return_value = None

        response = client.get('/api/health')

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['services']['odoo'] == 'disconnected'
    assert data['services']['supabase'] == 'disconnected'


def test_health_odoo_error_still_returns_200(client):
    with patch('app.web.routes.OdooRepository') as mock_odoo_cls, \
         patch('app.web.routes.SupabaseClient') as mock_supabase:
        mock_odoo_cls.side_effect = Exception('connection refused')
        mock_supabase.get_client.return_value = MagicMock()

        response = client.get('/api/health')

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['services']['odoo'] == 'error'
