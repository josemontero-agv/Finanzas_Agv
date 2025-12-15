# 📁 Estructura del Proyecto - Finanzas AGV

## Árbol de Archivos Completo

```
Finanzas_Agv/
│
├── 📄 Dockerfile                       # Definición de imagen Docker (App + Worker)
├── 📄 docker-compose.yml               # Orquestación de servicios (Web, Redis, Worker)
├── 📄 GUIA_INSTALACION_DOCKER.md       # Guía paso a paso para Docker
├── 📄 README.md                        # Documentación principal
├── 📄 config.py                        # Configuraciones (Dev/Prod/Test)
├── 📄 run.py                           # Punto de entrada de la aplicación
├── 📄 celery_worker.py                 # Punto de entrada para Celery
├── 📄 requirements.txt                 # Dependencias del proyecto
├── 📄 .gitignore                       # Archivos ignorados por Git
│
├── 📄 .env.desarrollo                  # ⚠️ CREAR MANUALMENTE - Variables de desarrollo
├── 📄 .env.produccion                  # ⚠️ CREAR MANUALMENTE - Variables de producción
│
├── 📁 docs/                            # 📚 Documentación completa del proyecto
│   ├── 📄 index.md                     # Índice principal
│   ├── 📄 ESTRUCTURA_PROYECTO.md       # Este archivo
│   ├── 📁 arquitectura/                # Documentación arquitectónica
│   │   ├── ARQUITECTURA_ACTUAL_DOCKER.md # 🆕 Arquitectura Docker + Celery
│   │   └── ...
│   └── ...
│
├── 📁 scripts/                         # Scripts de utilidad y ETL
│   ├── 📁 etl/
│   │   ├── etl_sync_threading.py       # Script principal de sincronización
│   │   └── ...
│   └── ...
│
└── 📁 app/                             # Código fuente de la aplicación
    │
    ├── 📄 __init__.py                  # Factory pattern y registro de Celery
    ├── 📄 tasks.py                     # 🆕 Definición de tareas asíncronas (ETL)
    │
    ├── 📁 core/                        # Componentes core compartidos
    │   ├── 📄 celery_utils.py          # Configuración de Celery
    │   ├── 📄 odoo.py                  # Repositorio Odoo
    │   └── 📄 supabase.py              # Cliente Supabase
    │
    ├── 📁 auth/                        # Módulo de Autenticación
    │
    ├── 📁 collections/                 # Módulo de Cobranzas
    │
    ├── 📁 treasury/                    # Módulo de Tesorería
    │   ├── 📄 __init__.py
    │   ├── 📄 routes.py                # Endpoints (CxP y Bancos)
    │   └── 📄 services.py              # Lógica de negocio
    │
    ├── 📁 ...                          # Otros módulos (emails, exports, etc.)
    │
    └── 📁 templates/                   # Templates HTML
        ├── 📄 base.html                # Template base
        ├── 📁 treasury/
        │   ├── report_account42.html       # Reporte CxP (limpio)
        │   └── report_supplier_banks.html  # 🆕 Reporte Cuentas Bancarias
        └── ...
```

## 📊 Componentes por Capa

### Capa de Infraestructura (Docker)
- `docker-compose.yml` - Define servicios: `web`, `worker`, `redis`
- `Dockerfile` - Construye el entorno Python unificado
- `redis` - Servicio de caché y broker de mensajes

### Capa de Aplicación
- `run.py` - Servidor Web (Gunicorn/Flask)
- `celery_worker.py` - Servidor de Tareas (Celery)
- `app/tasks.py` - Definición de tareas asíncronas (ETLs)

### Capa Core
- `app/core/odoo.py` - Conexión síncrona a Odoo (XML-RPC)
- `app/core/supabase.py` - Conexión a base de datos analítica

### Capa de Módulos

#### 🏦 Módulo Treasury (Tesorería)
```
app/treasury/
├── services.py    → Lógica de negocio
│                    - get_report_lines_paginated()
│                    - get_supplier_bank_accounts() 🆕
└── routes.py      → Endpoints
                     - GET /api/v1/treasury/report/account42
                     - GET /api/v1/treasury/report/supplier-banks 🆕
```

## 🔄 Flujo de Datos (Arquitectura AP)

```
1. Odoo (Fuente)
   ↓ (Sincronización Asíncrona vía Celery Worker)
2. ETL Script (scripts/etl/etl_sync_threading.py)
   ↓ (Escritura)
3. Supabase (Almacén Intermedio)
   ↓ (Lectura Rápida)
4. Flask App (Web Container)
   ↓
5. Usuario
```

## 🚀 Comandos Útiles (Docker)

```bash
# Iniciar todo el stack
docker-compose up --build

# Ver logs en tiempo real
docker-compose logs -f

# Detener servicios
docker-compose down
```

---

**Última actualización:** Diciembre 2024 (Migración a Docker)
