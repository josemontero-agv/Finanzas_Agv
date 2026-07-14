#!/usr/bin/env bash
# Smoke test post-deploy contra el backend en Render (o staging).
#
# Uso:
#   ./scripts/ci/smoke_test.sh https://finanzas-agv-backend.onrender.com

set -euo pipefail

BACKEND_URL="${1:-${BACKEND_URL:-}}"

if [[ -z "${BACKEND_URL}" ]]; then
  echo "ERROR: Debe indicar BACKEND_URL como argumento o variable de entorno." >&2
  echo "Uso: $0 <BACKEND_URL>" >&2
  exit 1
fi

BACKEND_URL="${BACKEND_URL%/}"
HEALTH_URL="${BACKEND_URL}/api/health"

echo "========================================"
echo " Post-deploy smoke test"
echo " URL: ${HEALTH_URL}"
echo "========================================"

http_code="$(curl -sS -o /tmp/smoke_health.json -w "%{http_code}" "${HEALTH_URL}")"

if [[ "${http_code}" != "200" ]]; then
  echo "ERROR: /api/health respondió HTTP ${http_code}" >&2
  cat /tmp/smoke_health.json >&2 || true
  exit 1
fi

if ! python - <<'PY'
import json
import sys

with open("/tmp/smoke_health.json", encoding="utf-8") as f:
    data = json.load(f)

status = data.get("status")
services = data.get("services") or {}

if status != "healthy":
    print(f"ERROR: status={status!r}, se esperaba 'healthy'", file=sys.stderr)
    sys.exit(1)

for name in ("odoo", "supabase"):
    state = services.get(name)
    if state not in ("connected", "disconnected", "error"):
        print(f"ERROR: services.{name}={state!r} inesperado", file=sys.stderr)
        sys.exit(1)
    print(f"  services.{name}: {state}")

print("Smoke test OK: /api/health healthy")
PY
then
  cat /tmp/smoke_health.json >&2 || true
  exit 1
fi
