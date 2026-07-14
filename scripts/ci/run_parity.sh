#!/usr/bin/env bash
# Paridad Odoo vs Supabase (Cobranzas) para CI/GitHub Actions.
# Inyecta secrets como variables de entorno y ejecuta test_collections_parity.py.
#
# Uso local:
#   export ODOO_URL=... ODOO_DB=... ODOO_USER=... ODOO_PASSWORD=...
#   export SUPABASE_DB_URI=... SUPABASE_URL=... SUPABASE_KEY=...
#   ./scripts/ci/run_parity.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

required_vars=(
  ODOO_URL
  ODOO_DB
  ODOO_USER
  ODOO_PASSWORD
  SUPABASE_DB_URI
  SUPABASE_URL
  SUPABASE_KEY
)

missing=()
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    missing+=("${var}")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "ERROR: Faltan variables de entorno requeridas: ${missing[*]}" >&2
  exit 1
fi

export APP_ENV=production

echo "========================================"
echo " Paridad Cobranzas: Odoo vs Supabase"
echo " APP_ENV=production"
echo "========================================"

python test_collections_parity.py --env produccion
