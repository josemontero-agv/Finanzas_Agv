<#
.SYNOPSIS
    Sincroniza documentacion del repositorio principal hacia la GitHub Wiki.

.DESCRIPTION
    Copia archivos Markdown de auditoria y changelog al repositorio local
    de la wiki, luego hace commit + push automatico.
    Usa la wiki local ya clonada en disco; si no existe, la clona una sola vez.

.PARAMETER WikiDir
    Ruta local del repositorio de la wiki.
    Por defecto usa la ubicacion estandar del proyecto.

.PARAMETER WikiRepo
    URL del repositorio remoto de la wiki (solo se usa si WikiDir no existe).

.PARAMETER DryRun
    Muestra que se haria sin copiar ni hacer push.

.PARAMETER NoPush
    Hace commit local pero no pushea a GitHub.

.EXAMPLE
    .\sync-wiki.ps1
    .\sync-wiki.ps1 -DryRun
    .\sync-wiki.ps1 -NoPush
#>

param(
    [string]$WikiDir  = "C:\Users\jmontero\Desktop\GitHub Proyectos_AGV\Wikis_De_Proyectos\Finanzas_Agv.wiki",
    [string]$WikiRepo = "https://github.com/josemontero-agv/Finanzas_Agv.wiki.git",
    [switch]$DryRun,
    [switch]$NoPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ─── helpers de log ───────────────────────────────────────────────────────────
function Log-Info  ([string]$msg) { Write-Host "[INFO]  $msg" -ForegroundColor Cyan   }
function Log-OK    ([string]$msg) { Write-Host "[OK]    $msg" -ForegroundColor Green  }
function Log-Warn  ([string]$msg) { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Log-Error ([string]$msg) { Write-Host "[ERROR] $msg" -ForegroundColor Red    }
function Log-Skip  ([string]$msg) { Write-Host "[SKIP]  $msg" -ForegroundColor DarkGray }
function Log-Dry   ([string]$msg) { Write-Host "[DRY]   $msg" -ForegroundColor Magenta }

# ─── directorio raiz del repo principal ───────────────────────────────────────
$RepoDir = $PSScriptRoot

# ─── mapeo de documentos ──────────────────────────────────────────────────────
# Clave   : ruta relativa al repo principal  (acepta wildcards para archivos con fecha)
# Valor   : nombre de pagina en la wiki      (sin ruta, solo nombre de archivo .md)
#
# Convencion de numeracion wiki:
#   01-19  documentacion base (ya existente)
#   20+    documentacion de auditoria / estado actual
# ─────────────────────────────────────────────────────────────────────────────
$PageMap = [ordered]@{
    # changelog siempre presente
    "changelog.md"                                                     = "Changelog.md"

    # archivos con fecha dinamica: se busca el mas reciente con Get-ChildItem
    "auditoria\ESTADO_IMPLEMENTACION_*.md"                             = "20_Estado_Implementacion.md"
    "auditoria\CAMBIOS_IMPLEMENTAR.md"                                 = "21_Cambios_a_Implementar.md"

    # informes de entrega
    "auditoria\Informe_Entrega\RESUMEN_EJECUTIVO_Directivos.md"        = "22_Resumen_Ejecutivo_Directivos.md"
    "auditoria\Informe_Entrega\CHECKLIST_IMPLEMENTACION.md"            = "23_Checklist_Implementacion.md"
    "auditoria\Informe_Entrega\INFORME_AUDITORIA_COMPLETA_*.md"        = "24_Informe_Auditoria_Completa.md"
    "auditoria\Informe_Entrega\INFORME_CODE_REVIEW_SENIOR_*.md"        = "25_Informe_Code_Review_Senior.md"
}

# ─── 1. Preparar repositorio local de la wiki ─────────────────────────────────
if (-not (Test-Path $WikiDir)) {
    Log-Info "Wiki local no encontrada. Clonando desde $WikiRepo ..."
    if ($DryRun) {
        Log-Dry "git clone $WikiRepo $WikiDir"
    } else {
        git clone $WikiRepo $WikiDir
        if ($LASTEXITCODE -ne 0) { Log-Error "Fallo al clonar la wiki."; exit 1 }
    }
} else {
    Log-Info "Wiki local encontrada en: $WikiDir"
    Log-Info "Actualizando con git pull..."
    if ($DryRun) {
        Log-Dry "git -C `"$WikiDir`" pull"
    } else {
        $pullOutput = git -C $WikiDir pull 2>&1
        if ($LASTEXITCODE -ne 0) {
            Log-Warn "git pull reporto problemas: $pullOutput"
        } else {
            Log-OK "Pull exitoso: $pullOutput"
        }
    }
}

# ─── 2. Copiar archivos ────────────────────────────────────────────────────────
$copiedFiles = @()
$missingFiles = @()

foreach ($pattern in $PageMap.Keys) {
    $destName = $PageMap[$pattern]
    $destPath = Join-Path $WikiDir $destName

    # Resolver wildcard: tomar el archivo mas reciente si hay varios
    $fullPattern = Join-Path $RepoDir $pattern
    $candidates = @(Get-ChildItem -Path (Split-Path $fullPattern -Parent) `
                                 -Filter (Split-Path $fullPattern -Leaf) `
                                 -ErrorAction SilentlyContinue |
                   Sort-Object LastWriteTime -Descending)

    if ($candidates.Count -eq 0) {
        Log-Warn "No encontrado (se omite): $pattern"
        $missingFiles += $pattern
        continue
    }

    $srcFile = $candidates[0]

    if ($DryRun) {
        Log-Dry "COPIAR: $($srcFile.FullName) → $destName"
    } else {
        Copy-Item -Path $srcFile.FullName -Destination $destPath -Force
        Log-OK "Copiado: $($srcFile.Name) → $destName"
    }
    $copiedFiles += $destName
}

# ─── 3. Actualizar seccion de ultimo sync en Home.md ──────────────────────────
$homePath = Join-Path $WikiDir "Home.md"
$fecha = Get-Date -Format "yyyy-MM-dd HH:mm"
$syncBlock = @"

---
<!-- SYNC_AUTO_START -->
## Ultimo sync desde repositorio principal

**Fecha:** $fecha  
**Archivos sincronizados:** $($copiedFiles.Count)  
$(if ($copiedFiles.Count -gt 0) { ($copiedFiles | ForEach-Object { "- $_" }) -join "`n" })
<!-- SYNC_AUTO_END -->
"@

if (Test-Path $homePath) {
    $homeContent = Get-Content $homePath -Raw -Encoding UTF8

    # Reemplazar bloque previo si existe
    if ($homeContent -match "(?s)<!-- SYNC_AUTO_START -->.*<!-- SYNC_AUTO_END -->") {
        $newContent = $homeContent -replace "(?s)\n*---\n<!-- SYNC_AUTO_START -->.*<!-- SYNC_AUTO_END -->", $syncBlock
    } else {
        $newContent = $homeContent + $syncBlock
    }

    if ($DryRun) {
        Log-Dry "ACTUALIZAR Home.md con fecha de sync: $fecha"
    } else {
        Set-Content -Path $homePath -Value $newContent -Encoding UTF8 -NoNewline
        Log-OK "Home.md actualizado con fecha de sync."
    }
}

# ─── 4. Commit ────────────────────────────────────────────────────────────────
if ($DryRun) {
    Log-Dry "git -C `"$WikiDir`" add -A"
    Log-Dry "git -C `"$WikiDir`" commit -m `"docs: sync desde repo principal [$fecha]`""
    Log-Dry "git -C `"$WikiDir`" push"
    Log-Info "--- DryRun finalizado. No se realizaron cambios. ---"
    exit 0
}

git -C $WikiDir add -A

# Verificar si hay cambios reales antes de commitear
$statusOutput = git -C $WikiDir status --porcelain 2>&1
if ([string]::IsNullOrWhiteSpace($statusOutput)) {
    Log-Skip "Sin cambios detectados. No se genera commit."
    exit 0
}

$commitMsg = "docs: sync desde repo principal [$fecha]"
git -C $WikiDir commit -m $commitMsg
if ($LASTEXITCODE -ne 0) {
    Log-Error "Fallo al hacer commit."
    exit 1
}
Log-OK "Commit realizado: $commitMsg"

# ─── 5. Push ──────────────────────────────────────────────────────────────────
if ($NoPush) {
    Log-Warn "NoPush activado: commit local listo pero NO se pusheo a GitHub."
    exit 0
}

Log-Info "Pusheando a GitHub Wiki..."
git -C $WikiDir push
if ($LASTEXITCODE -ne 0) {
    Log-Error "Fallo el push. Verifica credenciales o conexion."
    exit 1
}

Log-OK "Wiki sincronizada correctamente en GitHub."

# ─── Resumen final ────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkCyan
Write-Host "  SYNC COMPLETADO  [$fecha]" -ForegroundColor Cyan
Write-Host "  Archivos copiados : $($copiedFiles.Count)" -ForegroundColor Green
if ($missingFiles.Count -gt 0) {
    Write-Host "  Archivos faltantes: $($missingFiles.Count)" -ForegroundColor Yellow
    $missingFiles | ForEach-Object { Write-Host "    - $_" -ForegroundColor Yellow }
}
Write-Host "═══════════════════════════════════════════" -ForegroundColor DarkCyan
