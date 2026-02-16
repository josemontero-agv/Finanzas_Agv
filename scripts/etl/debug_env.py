# -*- coding: utf-8 -*-
"""
Debug de variables de entorno y conectividad Supabase.

Hace validaciones similares a las pruebas manuales:
1) Carga .env backend + frontend/.env.local
2) Valida presencia de variables clave (sin exponer secretos)
3) Prueba auth settings con Service Key y Anon/Publishable Key
4) Prueba disponibilidad de tablas esperadas via REST
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from requests.exceptions import SSLError
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def mask(value: str, keep: int = 6) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return f"{value[:keep]}...({len(value)} chars)"


def load_env_files(base_dir: Path, env_suffix: str = "produccion") -> None:
    env_files = [
        base_dir / f".env.{env_suffix}",
        base_dir / f".env.supabase.{env_suffix}",
        base_dir / "frontend" / ".env.local",
    ]

    print("\n[ENV] Cargando archivos:")
    for env_file in env_files:
        exists = env_file.exists()
        print(f"  - {env_file}: {'OK' if exists else 'NO ENCONTRADO'}")
        if exists:
            load_dotenv(env_file, override=True)


def show_env_status() -> None:
    print("\n[ENV] Variables detectadas:")
    keys = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_DB_URI",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        "NEXT_PUBLIC_FLASK_API_URL",
    ]
    for key in keys:
        value = os.getenv(key, "")
        print(f"  - {key}: {'SI' if value else 'NO'} {mask(value)}")


def get_with_ssl_fallback(url: str, headers: dict, timeout: int = 30) -> tuple[requests.Response, bool]:
    try:
        return requests.get(url, headers=headers, timeout=timeout), True
    except SSLError:
        response = requests.get(url, headers=headers, timeout=timeout, verify=False)
        return response, False


def check_auth_settings() -> bool:
    supabase_url = os.getenv("SUPABASE_URL", "").strip().strip('"').strip("'")
    service_key = os.getenv("SUPABASE_KEY", "").strip().strip('"').strip("'")
    frontend_url = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "").strip().strip('"').strip("'")
    anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip().strip('"').strip("'")

    if not supabase_url or not service_key:
        print("\n[AUTH] Faltan SUPABASE_URL o SUPABASE_KEY para prueba backend.")
        return False
    if not frontend_url or not anon_key:
        print("\n[AUTH] Faltan NEXT_PUBLIC_SUPABASE_URL o NEXT_PUBLIC_SUPABASE_ANON_KEY para prueba frontend.")
        return False

    print("\n[AUTH] Prueba de llaves:")
    service_headers = {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
    anon_headers = {"apikey": anon_key, "Authorization": f"Bearer {anon_key}"}

    service_resp, service_secure = get_with_ssl_fallback(f"{supabase_url}/auth/v1/settings", service_headers)
    anon_resp, anon_secure = get_with_ssl_fallback(f"{frontend_url}/auth/v1/settings", anon_headers)

    print(
        f"  - Service Key /auth/v1/settings: {service_resp.status_code} "
        f"(SSL {'normal' if service_secure else 'inseguro'})"
    )
    print(
        f"  - Anon Key /auth/v1/settings:    {anon_resp.status_code} "
        f"(SSL {'normal' if anon_secure else 'inseguro'})"
    )

    same_url = supabase_url == frontend_url
    print(f"  - URL backend y frontend coinciden: {'SI' if same_url else 'NO'}")

    return service_resp.status_code == 200 and anon_resp.status_code == 200


def check_expected_tables() -> None:
    supabase_url = os.getenv("SUPABASE_URL", "").strip().strip('"').strip("'")
    service_key = os.getenv("SUPABASE_KEY", "").strip().strip('"').strip("'")
    anon_key = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "").strip().strip('"').strip("'")

    if not supabase_url or not service_key or not anon_key:
        print("\n[TABLES] Saltado: faltan variables para probar tablas.")
        return

    print("\n[TABLES] Verificando tablas esperadas en schema public:")
    tables = ["fact_moves", "fact_letters", "dim_partners"]
    for table in tables:
        path = f"{supabase_url}/rest/v1/{table}?select=*&limit=1"
        service_resp, _ = get_with_ssl_fallback(
            path, {"apikey": service_key, "Authorization": f"Bearer {service_key}"}
        )
        anon_resp, _ = get_with_ssl_fallback(
            path, {"apikey": anon_key, "Authorization": f"Bearer {anon_key}"}
        )
        print(f"  - {table}: service={service_resp.status_code} anon={anon_resp.status_code}")


def inspect_db_uri() -> None:
    db_uri = os.getenv("SUPABASE_DB_URI", "").strip().strip('"').strip("'")
    if not db_uri:
        print("\n[DB URI] SUPABASE_DB_URI no definida.")
        return

    parsed = urlparse(db_uri)
    print("\n[DB URI] Resumen:")
    print(f"  - scheme:   {parsed.scheme}")
    print(f"  - host:     {parsed.hostname}")
    print(f"  - port:     {parsed.port}")
    print(f"  - user:     {parsed.username}")
    print(f"  - password: {'SI' if parsed.password else 'NO'}")
    print(f"  - db:       {parsed.path}")


def main() -> None:
    base_dir = Path(__file__).resolve().parents[2]
    print("=== Diagnostico de entorno y Supabase ===")
    print(f"[INFO] Base dir: {base_dir}")

    load_env_files(base_dir, env_suffix="produccion")
    show_env_status()
    inspect_db_uri()

    auth_ok = check_auth_settings()
    check_expected_tables()

    print("\n[RESUMEN]")
    print(f"  - Credenciales Auth: {'OK' if auth_ok else 'FALLA'}")
    if not auth_ok:
        print("  - Revisa URL/keys en .env.supabase.produccion y frontend/.env.local")
    else:
        print("  - Si las tablas dan 404, falta crear/exponer tablas en schema public o revisar nombre/schema.")


if __name__ == "__main__":
    main()

