# Test de paridad Odoo vs Supabase (Cobranzas)
# Uso:
#   .\scripts\etl\run_parity.ps1
#   .\scripts\etl\run_parity.ps1 -Env desarrollo
#   .\scripts\etl\run_parity.ps1 -Env produccion

param(
    [ValidateSet("desarrollo", "produccion")]
    [string]$Env = "produccion"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonExe = Join-Path $RepoRoot "venv\Scripts\python.exe"
$ParityScript = Join-Path $RepoRoot "test_collections_parity.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "No se encontró el venv en $PythonExe. Cree el entorno: python -m venv venv; pip install -r requirements.txt"
}

if (-not (Test-Path $ParityScript)) {
    Write-Error "No se encontró test_collections_parity.py en la raíz del repo."
}

$appEnv = if ($Env -eq "produccion") { "production" } else { "development" }
$env:APP_ENV = $appEnv

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Paridad Cobranzas: Odoo vs Supabase" -ForegroundColor Cyan
Write-Host " --env $Env (APP_ENV=$appEnv)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $RepoRoot
try {
    & $PythonExe $ParityScript --env $Env
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
