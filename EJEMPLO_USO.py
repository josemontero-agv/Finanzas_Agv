# -*- coding: utf-8 -*-
"""
Ejemplo de uso de la API Finanzas AGV.

Este script muestra cómo consumir los endpoints de la API.
Requiere: pip install requests
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:5000"
API_VERSION = "/api/v1"


def print_response(title, response):
    """Helper para imprimir respuestas de forma legible."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


def ejemplo_info_api():
    """Obtener información general de la API."""
    response = requests.get(f"{BASE_URL}/")
    print_response("Información General de la API", response)


def ejemplo_login():
    """Ejemplo de login."""
    url = f"{BASE_URL}{API_VERSION}/auth/login"
    data = {
        "username": "usuario_ejemplo",
        "password": "contraseña_ejemplo"
    }
    response = requests.post(url, json=data)
    print_response("Login de Usuario", response)


def ejemplo_reporte_general():
    """Ejemplo de reporte general de cobranzas."""
    url = f"{BASE_URL}{API_VERSION}/collections/report/account12"
    params = {
        "date_from": "2024-01-01",
        "date_to": "2024-12-31",
        "limit": 10
    }
    response = requests.get(url, params=params)
    print_response("Reporte General de Cobranzas (Primeros 10)", response)


def ejemplo_reporte_nacional():
    """Ejemplo de reporte nacional."""
    url = f"{BASE_URL}{API_VERSION}/collections/report/national"
    params = {
        "date_from": "2024-01-01",
        "limit": 5
    }
    response = requests.get(url, params=params)
    print_response("Reporte Nacional de Cobranzas", response)


def ejemplo_reporte_internacional():
    """Ejemplo de reporte internacional con cálculos."""
    url = f"{BASE_URL}{API_VERSION}/collections/report/international"
    params = {
        "date_from": "2024-01-01",
        "limit": 5
    }
    response = requests.get(url, params=params)
    print_response("Reporte Internacional de Cobranzas", response)


def ejemplo_status_modulos():
    """Verificar el estado de todos los módulos."""
    modulos = ['auth', 'collections', 'treasury']
    
    for modulo in modulos:
        url = f"{BASE_URL}{API_VERSION}/{modulo}/status"
        response = requests.get(url)
        print_response(f"Estado del Módulo: {modulo.upper()}", response)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  EJEMPLOS DE USO - API FINANZAS AGV")
    print("="*60)
    print("\nAsegúrate de que la API esté corriendo:")
    print("  python run.py")
    print("\nPresiona Enter para continuar...")
    input()
    
    try:
        # Ejecutar ejemplos
        ejemplo_info_api()
        ejemplo_status_modulos()
        ejemplo_login()
        ejemplo_reporte_general()
        ejemplo_reporte_nacional()
        ejemplo_reporte_internacional()
        
        print("\n" + "="*60)
        print("  EJEMPLOS COMPLETADOS")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] No se pudo conectar a la API.")
        print("Asegúrate de que la API esté corriendo en http://localhost:5000")
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")

