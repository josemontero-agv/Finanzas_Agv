# -*- coding: utf-8 -*-
"""Paridad Odoo vs Supabase para Cobranzas (validación pre go-live).

Uso (desde la raíz del repo):
    venv\\Scripts\\python.exe test_collections_parity.py
    venv\\Scripts\\python.exe test_collections_parity.py --env desarrollo
    .\\scripts\\etl\\run_parity.ps1 -Env produccion

Exit code 0 si todos los escenarios MATCH; 1 si hay DIFF o error fatal.
Solo lectura hacia Odoo y Supabase.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, timedelta

_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

ENV_FILES = {
    'produccion': '.env.produccion',
    'desarrollo': '.env.desarrollo',
}

BASE_METRICS = ['count', 'debit', 'credit', 'balance', 'residual']
CUTOFF_METRICS = [
    'pending_cutoff',
    'amount_residual_historical',
    'paid_after_cutoff',
    'paid_before_cutoff',
]


def _parse_args():
    parser = argparse.ArgumentParser(
        description='Compara totales Cobranzas Odoo vs Supabase para varios escenarios.',
    )
    parser.add_argument(
        '--env',
        choices=('desarrollo', 'produccion'),
        default='produccion',
        help='Archivo .env a cargar (default: produccion -> .env.produccion)',
    )
    return parser.parse_args()


def _load_env(env_name: str) -> str:
    from dotenv import load_dotenv

    app_env = 'production' if env_name == 'produccion' else 'development'
    os.environ['APP_ENV'] = app_env

    env_file = ENV_FILES[env_name]
    env_path = os.path.join(_REPO_ROOT, env_file)
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f'[INIT] Configuración cargada desde {env_path} (APP_ENV={app_env})')
    else:
        print(f'[WARN] No se encontró {env_path}; se usan variables ya presentes en el entorno')
    return env_path


def _get_env_clean(key: str):
    val = os.getenv(key)
    return val.replace('"', '').replace("'", '') if val else None


def _residual_field(row: dict) -> float:
    if row.get('estado_historico'):
        return float(row.get('amount_residual_historical') or 0.0)
    return float(
        row.get('amount_residual_with_retention')
        or row.get('amount_residual')
        or row.get('line_amount_residual')
        or 0.0
    )


def _summarize(rows: list, *, has_cutoff: bool) -> dict:
    summary = {
        'count': len(rows),
        'debit': round(sum(float(r.get('debit') or 0) for r in rows), 2),
        'credit': round(sum(float(r.get('credit') or 0) for r in rows), 2),
        'balance': round(sum(float(r.get('balance') or 0) for r in rows), 2),
        'residual': round(sum(_residual_field(r) for r in rows), 2),
    }
    if has_cutoff:
        summary['pending_cutoff'] = round(
            sum(float(r.get('amount_residual_historical') or 0) for r in rows), 2,
        )
        summary['amount_residual_historical'] = summary['pending_cutoff']
        summary['paid_after_cutoff'] = round(
            sum(float(r.get('paid_after_cutoff') or 0) for r in rows), 2,
        )
        summary['paid_before_cutoff'] = round(
            sum(float(r.get('paid_before_cutoff') or 0) for r in rows), 2,
        )
    return summary


def _pct_diff(a: float, b: float) -> float:
    if a == 0 and b == 0:
        return 0.0
    base = abs(a) if abs(a) > 1e-9 else abs(b)
    if base < 1e-9:
        return 0.0
    return (b - a) / base * 100.0


def _print_table(label: str, odoo_summary: dict, supabase_summary: dict, metrics: list) -> bool:
    print(f'\n{"=" * 96}')
    print(f'ESCENARIO: {label}')
    print('=' * 96)

    header = f"{'Métrica':<28}{'Odoo':>18}{'Supabase':>18}{'Dif. abs.':>16}{'Dif. %':>10}"
    print(header)
    print('-' * len(header))

    all_match = True
    for key in metrics:
        a = odoo_summary.get(key, 0)
        b = supabase_summary.get(key, 0)
        diff = b - a
        pct = _pct_diff(a, b)
        if key == 'count':
            row_ok = int(a) == int(b)
            print(f'{key:<28}{a:>18.0f}{b:>18.0f}{diff:>16.0f}{pct:>9.2f}%')
        else:
            row_ok = abs(diff) < 0.01
            print(f'{key:<28}{a:>18,.2f}{b:>18,.2f}{diff:>16,.2f}{pct:>9.2f}%')
        if not row_ok:
            all_match = False

    verdict = 'MATCH' if all_match else 'DIFF'
    print(f'\nVeredicto: {verdict}')
    return all_match


def _compare(label: str, odoo_service, supabase_provider, odoo_kw: dict, supa_kw: dict):
    has_cutoff = bool(odoo_kw.get('cutoff_date') or supa_kw.get('cutoff_date'))
    metrics = BASE_METRICS + (CUTOFF_METRICS if has_cutoff else [])

    try:
        o_rows = odoo_service.get_report_lines(**odoo_kw) or []
    except Exception as e:
        print(f'\n[ERROR] Odoo ({label}): {type(e).__name__}: {e}')
        return False

    try:
        s_rows = supabase_provider.get_report_lines(**supa_kw) or []
    except Exception as e:
        print(f'\n[ERROR] Supabase ({label}): {type(e).__name__}: {e}')
        return False

    ot = _summarize(o_rows, has_cutoff=has_cutoff)
    st = _summarize(s_rows, has_cutoff=has_cutoff)
    return _print_table(label, ot, st, metrics)


def main() -> bool:
    args = _parse_args()
    _load_env(args.env)

    from app.collections.services import CollectionsService
    from app.collections.supabase_provider import CollectionsSupabaseProvider
    from app.core.odoo import OdooRepository

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
        print(f'[FATAL] Faltan variables Odoo: {missing}')
        return False

    if not supabase_db_uri:
        print('[FATAL] SUPABASE_DB_URI no está definida.')
        return False

    odoo_repo = OdooRepository(
        url=odoo_url, db=odoo_db, username=odoo_user, password=odoo_password,
    )
    if not odoo_repo.is_connected():
        print('[FATAL] No se pudo conectar a Odoo.')
        return False

    odoo_service = CollectionsService(odoo_repo)
    supabase_provider = CollectionsSupabaseProvider(supabase_db_uri)

    today = date.today()
    month_ago = (today - timedelta(days=30)).isoformat()
    today_iso = today.isoformat()
    cutoff = (today - timedelta(days=15)).isoformat()

    scenarios = [
        (
            'sin_fecha_limit_200',
            {'limit': 200},
            {'limit': 200},
        ),
        (
            f'ultimo_mes ({month_ago} .. {today_iso})',
            {'start_date': month_ago, 'end_date': today_iso, 'limit': 500},
            {'start_date': month_ago, 'end_date': today_iso, 'limit': 500},
        ),
        (
            f'con_cutoff (cutoff={cutoff})',
            {
                'date_cutoff_start': month_ago,
                'cutoff_date': cutoff,
                'include_reconciled': True,
                'limit': 500,
            },
            {
                'date_cutoff_start': month_ago,
                'cutoff_date': cutoff,
                'include_reconciled': True,
                'limit': 500,
            },
        ),
    ]

    results = []
    for name, ok, sk in scenarios:
        ok_match = _compare(name, odoo_service, supabase_provider, ok, sk)
        results.append((name, ok_match))

    matched = sum(1 for _, ok in results if ok)
    total = len(results)

    print(f'\n{"=" * 96}')
    print('RESUMEN FINAL')
    print('=' * 96)
    for name, ok in results:
        print(f'  {"MATCH" if ok else "DIFF":<6}  {name}')
    print(f'\n{matched}/{total} escenarios con totales idénticos')

    return matched == total


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
