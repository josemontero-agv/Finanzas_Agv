#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de prueba para el Modo Desarrollo de Correos (Windows).

Este script permite verificar que la configuración del modo desarrollo
esté funcionando correctamente antes de probar con la interfaz web.
"""

import os
import sys
from dotenv import load_dotenv

def test_dev_email_configuration():
    """Verifica la configuración del modo desarrollo de correos."""
    
    print("=" * 60)
    print("TEST DE CONFIGURACION - MODO DESARROLLO DE CORREOS")
    print("=" * 60)
    print()
    
    # Cargar variables de entorno
    base_path = os.path.dirname(__file__)
    env_files = [
        os.path.join(base_path, '.env.desarrollo'),
        os.path.join(base_path, '.env.supabase.desarrollo')
    ]
    
    print("Cargando archivos de configuracion:")
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            print(f"   [OK] {os.path.basename(env_file)}")
        else:
            print(f"   [WARN] {os.path.basename(env_file)} - No encontrado")
    print()
    
    # Verificar variables clave
    print("Verificando variables de entorno:")
    print()
    
    # Modo desarrollo
    dev_mode = os.getenv('DEV_EMAIL_MODE', 'False')
    dev_email = os.getenv('DEV_EMAIL_RECIPIENT', 'No configurado')
    
    print(f"   DEV_EMAIL_MODE: {dev_mode}")
    print(f"   DEV_EMAIL_RECIPIENT: {dev_email}")
    print()
    
    # Configuración SMTP
    mail_username = os.getenv('MAIL_USERNAME', 'No configurado')
    mail_server = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    mail_port = os.getenv('MAIL_PORT', '587')
    
    print(f"   MAIL_SERVER: {mail_server}")
    print(f"   MAIL_PORT: {mail_port}")
    print(f"   MAIL_USERNAME: {mail_username}")
    print(f"   MAIL_PASSWORD: {'***' if os.getenv('MAIL_PASSWORD') else 'No configurado'}")
    print()
    
    # Análisis de configuración
    print("=" * 60)
    print("ANALISIS DE CONFIGURACION")
    print("=" * 60)
    print()
    
    issues = []
    warnings = []
    
    # Verificar modo desarrollo
    if dev_mode.lower() == 'true':
        print("[OK] Modo Desarrollo: ACTIVADO")
        print(f"   -> Todos los correos se redirigiran a: {dev_email}")
        print()
        
        if dev_email == 'No configurado' or '@' not in dev_email:
            issues.append("DEV_EMAIL_RECIPIENT no esta configurado correctamente")
    else:
        warnings.append("Modo Desarrollo DESACTIVADO - Los correos se enviaran a destinatarios reales")
        print("[WARN] Modo Desarrollo: DESACTIVADO")
        print("   -> Los correos se enviaran a los destinatarios reales")
        print()
    
    # Verificar configuración SMTP
    if mail_username == 'No configurado':
        issues.append("MAIL_USERNAME no esta configurado")
    
    if not os.getenv('MAIL_PASSWORD'):
        issues.append("MAIL_PASSWORD no esta configurado")
    
    # Mostrar problemas
    if issues:
        print("[ERROR] PROBLEMAS ENCONTRADOS:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print()
    
    if warnings:
        print("[WARN] ADVERTENCIAS:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
        print()
    
    # Recomendaciones
    print("=" * 60)
    print("RECOMENDACIONES")
    print("=" * 60)
    print()
    
    if dev_mode.lower() != 'true':
        print("1. Para activar el modo desarrollo, agrega a .env.desarrollo:")
        print("   DEV_EMAIL_MODE=True")
        print("   DEV_EMAIL_RECIPIENT=josemontero2415@gmail.com")
        print()
    
    if issues:
        print("2. Configura las credenciales SMTP en .env.desarrollo:")
        print("   MAIL_USERNAME=tu-email@gmail.com")
        print("   MAIL_PASSWORD=tu-contrasena-de-aplicacion")
        print()
        print("3. Para generar una contrasena de aplicacion de Gmail:")
        print("   https://myaccount.google.com/apppasswords")
        print()
    
    if not issues and dev_mode.lower() == 'true':
        print("[OK] La configuracion parece correcta!")
        print()
        print("Proximos pasos:")
        print("   1. Inicia el servidor Flask: python run.py")
        print("   2. Inicia el frontend: cd frontend && npm run dev")
        print("   3. Ve a http://localhost:3000/letters")
        print("   4. Selecciona letras y envia correos de prueba")
        print("   5. Revisa tu email: " + dev_email)
        print()
    
    # Resumen final
    print("=" * 60)
    if issues:
        print("[ERROR] RESULTADO: Configuracion incompleta")
        print(f"   Se encontraron {len(issues)} problema(s)")
        return False
    elif warnings:
        print("[WARN] RESULTADO: Configuracion valida con advertencias")
        print(f"   Se encontraron {len(warnings)} advertencia(s)")
        return True
    else:
        print("[OK] RESULTADO: Configuracion correcta")
        return True


def show_example_email():
    """Muestra un ejemplo de cómo se verá el correo en modo desarrollo."""
    
    print()
    print("=" * 60)
    print("EJEMPLO DE CORREO EN MODO DESARROLLO")
    print("=" * 60)
    print()
    
    print("De: jose.montero@agrovetmarket.com")
    print("Para: josemontero2415@gmail.com")
    print("Asunto: [DEV - Original: cliente@agrovet.com] Letras Pendientes de Firma - Agrovet S.A.")
    print()
    print("-" * 60)
    print()
    print("Buenas tardes Estimada/o,")
    print()
    print("Se adjunta las letras para su pronta firma:")
    print()
    print("  * Letra L-2024001 - PEN 15,000.00 - Vence: 2024-03-15")
    print("  * Letra L-2024002 - PEN 22,500.00 - Vence: 2024-03-20")
    print()
    print("Por favor responder correo cuando se este enviando las letras firmadas.")
    print()
    print("Cordialmente,")
    print("Jose Montero | Asistente de Creditos y Cobranzas")
    print("(1) 2300 300 Anexo | +51 965 252 063 | jose.montero@agrovetmarket.com")
    print()
    print("-" * 60)
    print()


if __name__ == '__main__':
    try:
        success = test_dev_email_configuration()
        
        if success:
            show_example_email()
        
        print()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n[ERROR] Error ejecutando el test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
