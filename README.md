# Finanzas AGV - API REST

API REST para gestión financiera - Cobranzas y Tesorería

## 📋 Descripción

Aplicación Flask con arquitectura AP (Alta Disponibilidad) basada en Docker, Celery y Redis.
Permite la gestión de:
- **Cobranzas (Collections)**: Reportes de cuentas por cobrar, nacionales e internacionales
- **Tesorería (Treasury)**: Reportes de flujo de caja, CxP y cuentas bancarias
- **Ingeniería de Datos**: ETLs asíncronos Odoo -> Supabase

## 🏗️ Arquitectura

- **Frontend**: Flask + Jinja2 (Server Side Rendering) + HTMX/Alpine.js
- **Backend**: Flask API REST
- **Async Tasks**: Celery + Redis
- **Data Engineering**: ETLs Python con Threads
- **Infraestructura**: Docker Compose

## 🚀 Inicio Rápido (Docker)

La forma recomendada de ejecutar el proyecto es usando Docker.

### 1. Requisitos Previos
- Docker Desktop instalado y corriendo
- Archivo `.env.desarrollo` configurado

### 2. Ejecutar
```powershell
docker-compose up --build
```

Esto levantará automáticamente:
- 🌐 **Web**: Aplicación Flask en http://localhost:5000
- 🧠 **Redis**: Broker de mensajería y caché
- 👷 **Worker**: Procesador de tareas en segundo plano (ETLs)

Para detener: `Ctrl+C` o `docker-compose down`

---

## ⚙️ Instalación Manual (Legacy / Desarrollo sin Docker)

### 1. Crear entorno virtual
```bash
python -m venv venv
# Activar:
venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar
```bash
python run.py
```
*Nota: Requiere servidor Redis externo corriendo si se usa la configuración por defecto.*

## 🔧 Variables de Entorno

Crea un archivo `.env.desarrollo` con:

```ini
# Flask
SECRET_KEY=dev-secret
FLASK_ENV=development

# Odoo
ODOO_URL=https://tu-odoo.com
ODOO_DB=base_datos
ODOO_USER=usuario
ODOO_PASSWORD=clave

# Supabase (Data Warehouse)
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_KEY=tu_clave_anonima
SUPABASE_DB_URI=postgresql://...

# Redis & Celery (Docker internos)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

## 📚 Documentación Completa

Toda la documentación técnica se encuentra en la carpeta `docs/`:
- [Estructura del Proyecto](docs/ESTRUCTURA_PROYECTO.md)
- [Arquitectura Docker](docs/arquitectura/ARQUITECTURA_ACTUAL_DOCKER.md)
- [Guía de Instalación Docker](GUIA_INSTALACION_DOCKER.md)

## 📡 Endpoints Principales

### Cobranzas
- `GET /api/v1/collections/report/account12` - Reporte General
- `GET /api/v1/collections/report/national` - Reporte Nacional

### Tesorería
- `GET /api/v1/treasury/report/account42` - Reporte CxP
- `GET /api/v1/treasury/report/supplier-banks` - Cuentas Bancarias

## 🤝 Contribución

1. Crear rama `feature/nueva-funcionalidad`
2. Desarrollar y probar localmente con Docker
3. Crear Pull Request

---
**Finanzas AGV** - 2024
