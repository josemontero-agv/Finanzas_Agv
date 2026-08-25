# Diagnóstico de credenciales y consulta de lectura a Odoo (XML-RPC).
# Uso:
#   .\scripts\etl\check_odoo.ps1
#   .\scripts\etl\check_odoo.ps1 -Env desarrollo
#   .\scripts\etl\check_odoo.ps1 -Env produccion
#   .\scripts\etl\check_odoo.ps1 -Env produccion -Model account.move -Limit 3

param(
    [ValidateSet("desarrollo", "produccion")]
    [string]$Env = "desarrollo",
    [string]$Model = "account.move",
    [int]$Limit = 3
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonExe = Join-Path $RepoRoot "venv\Scripts\python.exe"
$CheckScript = Join-Path $RepoRoot "scripts\etl\check_odoo.py"

if (-not (Test-Path $PythonExe)) {
    Write-Error "No se encontró el venv en $PythonExe. Cree el entorno: python -m venv venv; pip install -r requirements.txt"
}

if (-not (Test-Path $CheckScript)) {
    Write-Error "No se encontró el script: $CheckScript"
}

$appEnv = if ($Env -eq "produccion") { "production" } else { "development" }
$env:APP_ENV = $appEnv

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Diagnóstico Odoo (XML-RPC, solo lectura)" -ForegroundColor Cyan
Write-Host " --env $Env (APP_ENV=$appEnv)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Push-Location $RepoRoot
try {
    & $PythonExe $CheckScript --env $Env --model $Model --limit $Limit
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
