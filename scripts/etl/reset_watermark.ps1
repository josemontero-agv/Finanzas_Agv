# Reset watermark ETL para re-sync histórico de líneas CxC (Cobranzas)
# Uso: .\scripts\etl\reset_watermark.ps1
#
# IMPORTANTE: Este script NO ejecuta SQL automáticamente contra Supabase.
# Imprime el DELETE para que lo ejecutes vía:
#   - Supabase Dashboard -> SQL Editor
#   - Supabase MCP (execute_sql) en Cursor
#   - psql con SUPABASE_DB_URI del .env activo

$ErrorActionPreference = "Stop"

$ModelName = "account.move.line.collections"

$Sql = @"
-- Reset watermark: próximo run_etl re-importará fact_move_lines completo (histórico)
DELETE FROM public.etl_sync_state
WHERE model_name = '$ModelName';

-- Verificar (debe devolver 0 filas para ese modelo):
SELECT model_name, last_synced_at
FROM public.etl_sync_state
WHERE model_name = '$ModelName';
"@

Write-Host "========================================" -ForegroundColor Yellow
Write-Host " Reset watermark ETL" -ForegroundColor Yellow
Write-Host " Modelo: $ModelName" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "Requiere acceso SQL a Supabase (Dashboard, MCP o psql)." -ForegroundColor Cyan
Write-Host "Tras ejecutar el SQL, correr:" -ForegroundColor Cyan
Write-Host "  .\scripts\etl\run_etl.ps1" -ForegroundColor White
Write-Host "  .\scripts\etl\run_parity.ps1" -ForegroundColor White
Write-Host ""
Write-Host "--- SQL (copiar y ejecutar en Supabase) ---" -ForegroundColor Green
Write-Host $Sql
Write-Host "--- fin SQL ---" -ForegroundColor Green
Write-Host ""

# Intento opcional con psql si está instalado y SUPABASE_DB_URI está definida
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$env:APP_ENV = "production"
$EnvFile = Join-Path $RepoRoot ".env.produccion"

if ((Get-Command psql -ErrorAction SilentlyContinue) -and (Test-Path $EnvFile)) {
    $uriLine = Get-Content $EnvFile | Where-Object { $_ -match '^\s*SUPABASE_DB_URI\s*=' } | Select-Object -First 1
    if ($uriLine -match '=\s*(.+)') {
        $dbUri = $Matches[1].Trim().Trim('"').Trim("'")
        Write-Host "psql detectado. Para ejecutar automáticamente:" -ForegroundColor DarkGray
        Write-Host "  `$env:APP_ENV='production'" -ForegroundColor DarkGray
        Write-Host "  psql `"$dbUri`" -c `"DELETE FROM public.etl_sync_state WHERE model_name = '$ModelName';`"" -ForegroundColor DarkGray
        Write-Host "(No se ejecuta automáticamente por seguridad.)" -ForegroundColor DarkGray
    }
}

exit 0
