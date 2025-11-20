# Script PowerShell para activar y desplegar documentación localmente

Write-Host "🚀 Activador de Documentación Finanzas AGV" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (!(Test-Path "mkdocs.yml")) {
    Write-Host "❌ Error: No se encuentra mkdocs.yml" -ForegroundColor Red
    Write-Host "   Asegúrate de estar en la carpeta Finanzas_Agv" -ForegroundColor Yellow
    exit 1
}

# Verificar Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Python no está instalado" -ForegroundColor Red
    Write-Host "   Instala Python 3.11 o superior" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Verificar/Instalar dependencias
Write-Host "📦 Verificando dependencias..." -ForegroundColor Cyan
try {
    python -c "import mkdocs" 2>$null
    Write-Host "   ✅ MkDocs ya instalado" -ForegroundColor Green
} catch {
    Write-Host "   Instalando MkDocs..." -ForegroundColor Yellow
    python -m pip install mkdocs mkdocs-material
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Selecciona una opción:" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "1) 🌐 Servir documentación localmente (http://127.0.0.1:8000)" -ForegroundColor White
Write-Host "2) 🔨 Construir sitio (sin servidor)" -ForegroundColor White
Write-Host "3) 🚀 Desplegar a GitHub Pages" -ForegroundColor White
Write-Host "4) ✅ Validar construcción (modo estricto)" -ForegroundColor White
Write-Host "5) ❌ Salir" -ForegroundColor White
Write-Host ""

$option = Read-Host "Opción [1-5]"

switch ($option) {
    "1" {
        Write-Host ""
        Write-Host "🌐 Iniciando servidor local..." -ForegroundColor Green
        Write-Host "   Presiona Ctrl+C para detener" -ForegroundColor Yellow
        Write-Host ""
        python -m mkdocs serve
    }
    "2" {
        Write-Host ""
        Write-Host "🔨 Construyendo sitio..." -ForegroundColor Cyan
        python -m mkdocs build
        Write-Host "✅ Sitio construido en: site/" -ForegroundColor Green
    }
    "3" {
        Write-Host ""
        Write-Host "🚀 Desplegando a GitHub Pages..." -ForegroundColor Cyan
        python -m mkdocs gh-deploy --force --clean --verbose
        Write-Host "✅ Desplegado exitosamente" -ForegroundColor Green
    }
    "4" {
        Write-Host ""
        Write-Host "✅ Validando construcción..." -ForegroundColor Cyan
        python -m mkdocs build --strict
        Write-Host "✅ Validación exitosa" -ForegroundColor Green
    }
    "5" {
        Write-Host "👋 Saliendo..." -ForegroundColor Yellow
        exit 0
    }
    default {
        Write-Host "❌ Opción inválida" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Presiona Enter para salir..." -ForegroundColor Gray
Read-Host

