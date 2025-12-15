# 🚀 Scripts de Activación de Documentación

Este directorio contiene scripts para facilitar el trabajo con la documentación.

## 📝 Archivos Disponibles

### `activate-docs.ps1` (Windows PowerShell)
Script interactivo para Windows con menú de opciones.

### `activate-docs.sh` (Linux/Mac Bash)
Script interactivo para sistemas Unix con menú de opciones.

## 🎯 Uso Rápido

### En Windows:
```powershell
.\activate-docs.ps1
```

### En Linux/Mac:
```bash
chmod +x activate-docs.sh
./activate-docs.sh
```

## 📋 Opciones del Menú

1. **🌐 Servir localmente**: Inicia servidor en `http://127.0.0.1:8000`
2. **🔨 Construir sitio**: Genera HTML en carpeta `site/`
3. **🚀 Desplegar a GitHub Pages**: Publica automáticamente
4. **✅ Validar construcción**: Verifica errores antes de commit
5. **❌ Salir**: Cierra el script

## ⚡ Atajos Directos (sin menú)

### Servir localmente:
```bash
mkdocs serve
```

### Construir:
```bash
mkdocs build
```

### Desplegar:
```bash
mkdocs gh-deploy --force --clean
```

## 📚 Documentación Completa

Ver [Guía de GitHub Pages](github-pages-setup.md) para instrucciones detalladas.

