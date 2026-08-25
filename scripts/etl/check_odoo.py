# -*- coding: utf-8 -*-
"""
Diagnóstico de credenciales y consulta de lectura a Odoo (XML-RPC).

Confirma que ODOO_URL / ODOO_DB / ODOO_USER / ODOO_PASSWORD del .env activo
permiten autenticar y ejecutar una consulta de solo lectura (search_read).

Uso (desde la raíz del repo, con el venv activo):

    python scripts/etl/check_odoo.py
    python scripts/etl/check_odoo.py --env desarrollo
    python scripts/etl/check_odoo.py --env produccion
    python scripts/etl/check_odoo.py --model account.move --limit 3

Equivale en PowerShell:

    .\\scripts\\etl\\check_odoo.ps1
    .\\scripts\\etl\\check_odoo.ps1 -Env produccion

Solo lectura. No escribe nada en Odoo. No imprime la contraseña ni la API Key.
"""

from __future__ import annotations

import argparse
import os
import socket
import sys
import xmlrpc.client
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

DEFAULT_MODEL = "res.users"
DEFAULT_FIELDS = ("id", "name", "login")
BUSINESS_MODEL = "account.move"
BUSINESS_FIELDS = ("id", "name", "move_type")
DEFAULT_TIMEOUT = 30


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _mask_secret(value: str) -> str:
    if not value:
        return "(vacío)"
    return f"*** ({len(value)} chars)"


def _clean(value: str | None) -> str:
    if not value:
        return ""
    return value.strip().strip('"').strip("'")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Confirma autenticación y una consulta de lectura a Odoo con las credenciales del .env."
    )
    parser.add_argument(
        "--env",
        choices=("desarrollo", "produccion"),
        default=None,
        help="Archivo .env a cargar. Por defecto: APP_ENV/FLASK_ENV/ENV, o desarrollo.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Modelo extra a consultar con search_read (default: {BUSINESS_MODEL}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Límite de registros del search_read de confirmación (default: 3).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout de red en segundos (default: {DEFAULT_TIMEOUT}).",
    )
    return parser.parse_args()


def resolve_env_suffix(cli_env: str | None) -> str:
    if cli_env:
        return cli_env
    app_env = (
        os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or os.getenv("ENV") or "development"
    ).strip().lower()
    return "produccion" if app_env in ("production", "produccion") else "desarrollo"


def load_env(env_suffix: str) -> Path | None:
    from dotenv import load_dotenv

    env_path = _REPO_ROOT / f".env.{env_suffix}"
    if env_path.exists():
        load_dotenv(env_path, override=True)
        return env_path
    return None


def load_credentials() -> dict:
    return {
        "url": _clean(os.getenv("ODOO_URL")).rstrip("/"),
        "db": _clean(os.getenv("ODOO_DB")),
        "user": _clean(os.getenv("ODOO_USER")),
        "password": _clean(os.getenv("ODOO_PASSWORD")),
    }


def print_credential_status(creds: dict) -> list[str]:
    missing = []
    print("\n[ENV] Credenciales Odoo (secretos enmascarados):")
    print(f"  - ODOO_URL:      {creds['url'] or '(vacío)'}")
    print(f"  - ODOO_DB:       {creds['db'] or '(vacío)'}")
    print(f"  - ODOO_USER:     {creds['user'] or '(vacío)'}")
    print(f"  - ODOO_PASSWORD: {_mask_secret(creds['password'])}")
    for key, label in (
        ("url", "ODOO_URL"),
        ("db", "ODOO_DB"),
        ("user", "ODOO_USER"),
        ("password", "ODOO_PASSWORD"),
    ):
        if not creds[key]:
            missing.append(label)
    return missing


def _server_version(common: xmlrpc.client.ServerProxy) -> dict | str:
    try:
        return common.version()
    except Exception:
        return common.version_info()


def confirm_odoo(creds: dict, extra_model: str, limit: int) -> int:
    """
    Pasos de confirmación:
      1) version() — el servidor responde
      2) authenticate() — las credenciales son válidas
      3) res.users.read — execute_kw funciona
      4) search_read del modelo de negocio — la consulta de datos funciona
    """
    url = creds["url"]
    db = creds["db"]
    user = creds["user"]
    password = creds["password"]

    print("\n[1/4] Versión del servidor Odoo…")
    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
        version = _server_version(common)
    except Exception as exc:
        print(f"  FALLO: no se pudo contactar {url}/xmlrpc/2/common ({type(exc).__name__}: {exc})")
        return 1

    if isinstance(version, dict):
        server_serie = version.get("server_serie") or version.get("server_version") or version
        protocol = version.get("protocol_version", "?")
        print(f"  OK  server={server_serie}  protocol={protocol}")
    else:
        print(f"  OK  version={version}")

    print("\n[2/4] Autenticación XML-RPC…")
    try:
        uid = common.authenticate(db, user, password, {})
    except Exception as exc:
        print(f"  FALLO: authenticate() lanzó {type(exc).__name__}: {exc}")
        return 1

    if not uid:
        print("  FALLO: credenciales o API Key inválidas (authenticate devolvió False/None).")
        print("  Revisa ODOO_USER / ODOO_PASSWORD (o API Key) y ODOO_DB.")
        return 1
    print(f"  OK  uid={uid}  user={user}  db={db}")

    print("\n[3/4] Consulta res.users.read (usuario autenticado)…")
    try:
        models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
        users = models.execute_kw(
            db,
            uid,
            password,
            DEFAULT_MODEL,
            "read",
            [[uid]],
            {"fields": list(DEFAULT_FIELDS)},
        )
    except xmlrpc.client.Fault as exc:
        print(f"  FALLO: Fault Odoo en res.users.read: {exc.faultString}")
        return 1
    except Exception as exc:
        print(f"  FALLO: res.users.read ({type(exc).__name__}: {exc})")
        return 1

    if not users:
        print("  FALLO: authenticate OK pero res.users.read no devolvió el usuario.")
        return 1

    current = users[0]
    print(
        f"  OK  id={current.get('id')}  name={current.get('name')}  login={current.get('login')}"
    )

    print(f"\n[4/4] Consulta {extra_model}.search_read (limit={limit})…")
    fields = list(BUSINESS_FIELDS) if extra_model == BUSINESS_MODEL else ["id", "name"]
    try:
        rows = models.execute_kw(
            db,
            uid,
            password,
            extra_model,
            "search_read",
            [[]],
            {"fields": fields, "limit": max(1, limit), "order": "id desc"},
        )
        count = models.execute_kw(
            db,
            uid,
            password,
            extra_model,
            "search_count",
            [[]],
        )
    except xmlrpc.client.Fault as exc:
        print(f"  FALLO: Fault Odoo en {extra_model}: {exc.faultString}")
        return 1
    except Exception as exc:
        print(f"  FALLO: {extra_model}.search_read ({type(exc).__name__}: {exc})")
        return 1

    print(f"  OK  search_count={count}  filas_devueltas={len(rows or [])}")
    for row in (rows or [])[:limit]:
        preview = "  ".join(f"{k}={row.get(k)}" for k in fields if k in row)
        print(f"    · {preview}")

    print("\n[RESUMEN] Conexión, autenticación y consulta a Odoo: OK")
    return 0


def main() -> int:
    _configure_stdio()
    args = parse_args()
    env_suffix = resolve_env_suffix(args.env)
    extra_model = (args.model or BUSINESS_MODEL).strip()
    socket.setdefaulttimeout(max(5, args.timeout))

    print("=== Diagnóstico de consulta a Odoo ===")
    print(f"[INFO] Repo: {_REPO_ROOT}")
    print(f"[INFO] Entorno: {env_suffix}  timeout={args.timeout}s")

    env_path = load_env(env_suffix)
    if env_path:
        print(f"[INFO] Cargado: {env_path}")
    else:
        print(f"[WARN] No se encontró .env.{env_suffix}; se usan variables ya presentes en el proceso")

    creds = load_credentials()
    missing = print_credential_status(creds)
    if missing:
        print(f"\n[RESUMEN] Faltan variables: {', '.join(missing)}")
        return 1

    return confirm_odoo(creds, extra_model=extra_model, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
