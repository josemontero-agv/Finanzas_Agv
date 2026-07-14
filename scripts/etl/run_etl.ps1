# Sincronización ETL Odoo -> Supabase (APP_ENV=production -> .env.produccion)
# Uso: .\scripts\etl\run_etl.ps1

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonExe = Join-Path $RepoRoot "venv\Scripts\python.exe"
$EtlScript = Join-Path $RepoRoot "scripts\etl\etl_sync_threading.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "No se encontró el venv en $PythonExe. Cree el entorno: python -m venv venv; pip install -r requirements.txt"
}

if (-not (Test-Path $EtlScript)) {
    Write-Error "No se encontró el script ETL: $EtlScript"
}

$env:APP_ENV = "production"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ETL Odoo -> Supabase" -ForegroundColor Cyan
Write-Host " APP_ENV=production (.env.produccion)" -ForegroundColor Cyan
Write-Host " Repo: $RepoRoot" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $RepoRoot
try {
    & $PythonExe $EtlScript
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
