#!/usr/bin/env bash
# Script para activar y desplegar documentación localmente

set -e  # Salir si hay errores

echo "🚀 Activador de Documentación Finanzas AGV"
echo "=========================================="
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "mkdocs.yml" ]; then
    echo "❌ Error: No se encuentra mkdocs.yml"
    echo "   Asegúrate de estar en la carpeta Finanzas_Agv"
    exit 1
fi

# Verificar Python
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python no está instalado"
    echo "   Instala Python 3.11 o superior"
    exit 1
fi

PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "✅ Python encontrado: $($PYTHON_CMD --version)"
echo ""

# Instalar dependencias si no existen
echo "📦 Verificando dependencias..."
if ! $PYTHON_CMD -c "import mkdocs" 2>/dev/null; then
    echo "   Instalando MkDocs..."
    $PYTHON_CMD -m pip install mkdocs mkdocs-material
else
    echo "   ✅ MkDocs ya instalado"
fi

echo ""
echo "=========================================="
echo "Selecciona una opción:"
echo "=========================================="
echo "1) 🌐 Servir documentación localmente (http://127.0.0.1:8000)"
echo "2) 🔨 Construir sitio (sin servidor)"
echo "3) 🚀 Desplegar a GitHub Pages"
echo "4) ✅ Validar construcción (modo estricto)"
echo "5) ❌ Salir"
echo ""

read -p "Opción [1-5]: " option

case $option in
    1)
        echo ""
        echo "🌐 Iniciando servidor local..."
        echo "   Presiona Ctrl+C para detener"
        echo ""
        $PYTHON_CMD -m mkdocs serve
        ;;
    2)
        echo ""
        echo "🔨 Construyendo sitio..."
        $PYTHON_CMD -m mkdocs build
        echo "✅ Sitio construido en: site/"
        ;;
    3)
        echo ""
        echo "🚀 Desplegando a GitHub Pages..."
        $PYTHON_CMD -m mkdocs gh-deploy --force --clean --verbose
        echo "✅ Desplegado exitosamente"
        ;;
    4)
        echo ""
        echo "✅ Validando construcción..."
        $PYTHON_CMD -m mkdocs build --strict
        echo "✅ Validación exitosa"
        ;;
    5)
        echo "👋 Saliendo..."
        exit 0
        ;;
    *)
        echo "❌ Opción inválida"
        exit 1
        ;;
esac

