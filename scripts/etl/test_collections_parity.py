# -*- coding: utf-8 -*-
"""
Script standalone de paridad Odoo vs Supabase para Cobranzas (Fase 3 - piloto).

Compara CollectionsService.get_report_lines (Odoo en vivo, SOLO LECTURA) contra
CollectionsSupabaseProvider.get_report_lines (tablas pobladas por
scripts/etl/etl_sync_threading.py) para varias combinaciones de filtros, e
imprime un reporte de diferencias (conteo de filas y sumas de debit/credit/
balance/residual) para decidir si es seguro activar COLLECTIONS_SOURCE=supabase
en producción.

No usa pytest a propósito: no hay convención de tests establecida en el repo
(no existe carpeta tests/), así que se prioriza un script ejecutable simple con
print() claros sobre montar infraestructura de tests nueva.

Uso (desde la raíz del repo, con el venv activo):
    $env:APP_ENV="production"
    venv\\Scripts\\python.exe scripts\\etl\\test_collections_parity.py

Solo lectura hacia Odoo (search_read) y hacia Supabase (SELECT). No escribe nada.
"""

import os
import sys
from datetime import date, timedelta

# Permite ejecutar el script directamente (python scripts/etl/test_collections_parity.py)
# sin depender de que el paquete "app" esté instalado; agrega la raíz del repo al path.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def _load_env():
    """Mismo patrón que etl_sync_threading._load_env_if_standalone(): carga
    .env.produccion si APP_ENV=production (o no está definido -> default acá
    a production, ya que este script es específicamente para probar contra
    Odoo producción según lo acordado)."""
    from dotenv import load_dotenv

    app_env = (os.getenv('APP_ENV') or 'production').lower()
    env_file = '.env.produccion' if app_env == 'production' else '.env.desarrollo'
    env_path = os.path.join(_REPO_ROOT, env_file)
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"[INIT] Configuración cargada desde {env_path}")
    else:
        print(f"[WARN] No se encontró {env_path}, se usan variables ya presentes en el entorno")


def _get_env_clean(key):
    val = os.getenv(key)
    return val.replace('"', '').replace("'", '') if val else None


FIELDS_TO_COMPARE = ['debit', 'credit', 'balance']


def _residual_field(row):
    """Campo de residual relevante: amount_residual_with_retention (vive normal)
    o amount_residual_historical (cuando hay cutoff_date), igual en ambas fuentes."""
    if row.get('estado_historico'):
        return float(row.get('amount_residual_historical') or 0.0)
    return float(row.get('amount_residual_with_retention') or 0.0)


def _summarize(rows):
    summary = {'count': len(rows)}
    for f in FIELDS_TO_COMPARE:
        summary[f] = sum(float(r.get(f) or 0.0) for r in rows)
    summary['residual'] = sum(_residual_field(r) for r in rows)
    return summary


def _pct_diff(a, b):
    if a == 0 and b == 0:
        return 0.0
    base = abs(a) if abs(a) > 1e-9 else abs(b)
    if base < 1e-9:
        return 0.0
    return (b - a) / base * 100.0


def _print_comparison(title, odoo_rows, supabase_rows):
    print("\n" + "=" * 90)
    print(f"COMBINACIÓN: {title}")
    print("=" * 90)

    odoo_summary = _summarize(odoo_rows)
    supabase_summary = _summarize(supabase_rows)

    header = f"{'Métrica':<12}{'Odoo':>18}{'Supabase':>18}{'Dif. absoluta':>18}{'Dif. %':>12}"
    print(header)
    print("-" * len(header))
    for key in ['count', 'debit', 'credit', 'balance', 'residual']:
        a = odoo_summary[key]
        b = supabase_summary[key]
        diff = b - a
        pct = _pct_diff(a, b)
        if key == 'count':
            print(f"{key:<12}{a:>18.0f}{b:>18.0f}{diff:>18.0f}{pct:>11.2f}%")
        else:
            print(f"{key:<12}{a:>18,.2f}{b:>18,.2f}{diff:>18,.2f}{pct:>11.2f}%")

    return odoo_summary, supabase_summary


def _diagnose_discrepancies(odoo_rows, supabase_rows, max_examples=3):
    """Compara filas individuales por move_name para identificar causas raíz
    concretas de discrepancias (según lo pedido en el Paso 4.6 del plan)."""
    odoo_by_key = {}
    for r in odoo_rows:
        key = (r.get('move_name') or r.get('account.move/name') or '', r.get('name') or '')
        odoo_by_key.setdefault(key, []).append(r)

    supabase_by_key = {}
    for r in supabase_rows:
        key = (r.get('move_name') or r.get('account.move/name') or '', r.get('name') or '')
        supabase_by_key.setdefault(key, []).append(r)

    only_in_odoo = [k for k in odoo_by_key if k not in supabase_by_key]
    only_in_supabase = [k for k in supabase_by_key if k not in odoo_by_key]

    print(f"\n[DIAGNÓSTICO] Documentos solo en Odoo: {len(only_in_odoo)} | solo en Supabase: {len(only_in_supabase)}")

    for key in only_in_odoo[:max_examples]:
        row = odoo_by_key[key][0]
        print(
            f"  - Solo en Odoo -> move={key[0]!r} línea={key[1]!r} "
            f"account={row.get('account_id/code')!r} residual_odoo={_residual_field(row):.2f}"
        )

    for key in only_in_supabase[:max_examples]:
        row = supabase_by_key[key][0]
        print(
            f"  - Solo en Supabase -> move={key[0]!r} línea={key[1]!r} "
            f"account={row.get('account_id/code')!r} residual_supabase={_residual_field(row):.2f}"
        )

    common_keys = [k for k in odoo_by_key if k in supabase_by_key]
    mismatched = []
    for key in common_keys:
        a = _residual_field(odoo_by_key[key][0])
        b = _residual_field(supabase_by_key[key][0])
        if abs(a - b) > 0.01:
            mismatched.append((key, a, b))

    print(f"[DIAGNÓSTICO] Documentos en ambas fuentes con residual distinto: {len(mismatched)}")
    for key, a, b in mismatched[:max_examples]:
        print(f"  - move={key[0]!r} línea={key[1]!r} residual_odoo={a:.2f} residual_supabase={b:.2f} diff={b - a:.2f}")

    if only_in_odoo or only_in_supabase or mismatched:
        account_codes_123 = any(
            (odoo_by_key.get(k, [{}])[0].get('account_id/code') or '').startswith('123')
            for k in (only_in_odoo + [m[0] for m in mismatched])
        )
        if account_codes_123:
            print(
                "[HIPÓTESIS] Discrepancias concentradas en cuenta 123 (letras): "
                "coincide con la limitación conocida documentada en "
                "app/collections/supabase_provider.py (la trazabilidad factura-origen vía "
                "bill_form_id -> account.bill.form -> invoice_ids no se reproduce en Supabase; "
                "ver docstring del módulo)."
            )


def run():
    _load_env()

    from app.core.odoo import OdooRepository
    from app.collections.services import CollectionsService
    from app.collections.supabase_provider import CollectionsSupabaseProvider

    odoo_url = _get_env_clean('ODOO_URL')
    odoo_db = _get_env_clean('ODOO_DB')
    odoo_user = _get_env_clean('ODOO_USER')
    odoo_password = _get_env_clean('ODOO_PASSWORD')
    supabase_db_uri = _get_env_clean('SUPABASE_DB_URI')

    missing = [
        name for name, val in [
            ('ODOO_URL', odoo_url), ('ODOO_DB', odoo_db),
            ('ODOO_USER', odoo_user), ('ODOO_PASSWORD', odoo_password),
        ] if not val
    ]
    if missing:
        print(f"[FATAL] Faltan variables de entorno para Odoo: {missing}")
        sys.exit(1)

    print("[INIT] Conectando a Odoo (solo lectura)...")
    odoo_repo = OdooRepository(url=odoo_url, db=odoo_db, username=odoo_user, password=odoo_password)
    if not odoo_repo.is_connected():
        print("[FATAL] No se pudo conectar a Odoo. Abortando.")
        sys.exit(1)
    print("[OK] Conectado a Odoo.")

    odoo_service = CollectionsService(odoo_repo)

    supabase_provider = None
    supabase_error = None
    if not supabase_db_uri:
        supabase_error = "SUPABASE_DB_URI no está definida en el entorno."
    else:
        try:
            supabase_provider = CollectionsSupabaseProvider(supabase_db_uri)
            # Prueba de conectividad mínima antes de usarlo en los escenarios.
            test_conn = supabase_provider._connect()
            test_conn.close()
            print("[OK] Conexión a Supabase (SUPABASE_DB_URI) verificada.")
        except Exception as e:
            # No se incluye str(e): los errores de DSN de psycopg2 pueden citar
            # fragmentos literales de la connection string (que puede contener
            # credenciales) dentro del propio mensaje de excepción.
            supabase_error = f"{type(e).__name__} (revisar formato/validez de SUPABASE_DB_URI sin exponerla en logs)"

    if supabase_error:
        print(f"\n[BLOQUEO] No se puede usar CollectionsSupabaseProvider: {supabase_error}")
        print(
            "[BLOQUEO] Se ejecutará SOLO el lado Odoo de cada combinación para dejar constancia "
            "de que ese camino funciona; la comparación de paridad real queda pendiente hasta "
            "resolver el acceso a Supabase (ver resumen final)."
        )

    today = date.today()
    last_month_start = (today - timedelta(days=30)).isoformat()
    today_iso = today.isoformat()
    cutoff = (today - timedelta(days=15)).isoformat()

    scenarios = [
        {'title': 'Sin filtros de fecha, limit=200', 'kwargs': {'limit': 200}},
        {'title': f'Rango de fechas acotado ({last_month_start} a {today_iso}), sin cutoff',
         'kwargs': {'start_date': last_month_start, 'end_date': today_iso, 'limit': 0}},
        {'title': f'Con cutoff_date={cutoff} (dentro del rango del último mes)',
         'kwargs': {'date_cutoff_start': last_month_start, 'cutoff_date': cutoff,
                    'include_reconciled': True, 'limit': 0}},
    ]

    results = []
    for scenario in scenarios:
        title = scenario['title']
        kwargs = scenario['kwargs']

        print(f"\n[RUN] Odoo: {title} ...")
        odoo_rows = odoo_service.get_report_lines(**kwargs)
        print(f"[OK] Odoo devolvió {len(odoo_rows)} filas.")

        if supabase_provider is not None:
            print(f"[RUN] Supabase: {title} ...")
            supabase_rows = supabase_provider.get_report_lines(**kwargs)
            print(f"[OK] Supabase devolvió {len(supabase_rows)} filas.")
        else:
            supabase_rows = []

        odoo_summary, supabase_summary = _print_comparison(title, odoo_rows, supabase_rows)
        results.append((title, odoo_summary, supabase_summary))

        if supabase_provider is not None:
            _diagnose_discrepancies(odoo_rows, supabase_rows)

    print("\n" + "=" * 90)
    print("RESUMEN FINAL DE PARIDAD")
    print("=" * 90)
    for title, odoo_summary, supabase_summary in results:
        estado = "OK" if odoo_summary == supabase_summary else "DIFERENCIAS" if supabase_provider else "NO COMPARADO (Supabase no disponible)"
        print(f"- {title}: {estado}")


if __name__ == '__main__':
    run()
