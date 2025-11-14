# 📁 Estructura del Proyecto - Finanzas AGV

## Árbol de Archivos Completo

```
Finanzas_Agv/
│
├── 📄 README.md                         # Documentación principal
├── 📄 INSTRUCCIONES_INICIO_RAPIDO.md   # Guía de inicio rápido
├── 📄 ESTRUCTURA_PROYECTO.md           # Este archivo
├── 📄 EJEMPLO_USO.py                   # Script de ejemplo de uso de la API
│
├── 📄 config.py                        # Configuraciones (Dev/Prod/Test)
├── 📄 run.py                           # Punto de entrada de la aplicación
├── 📄 requirements.txt                 # Dependencias del proyecto
├── 📄 .gitignore                       # Archivos ignorados por Git
│
├── 📄 .env.desarrollo                  # ⚠️ CREAR MANUALMENTE - Variables de desarrollo
├── 📄 .env.produccion                  # ⚠️ CREAR MANUALMENTE - Variables de producción
│
├── 📁 venv/                            # Entorno virtual (crear con: python -m venv venv)
│
└── 📁 app/                             # Código fuente de la aplicación
    │
    ├── 📄 __init__.py                  # Factory pattern (create_app)
    │
    ├── 📁 core/                        # Componentes core compartidos
    │   ├── 📄 __init__.py
    │   ├── 📄 odoo.py                  # OdooRepository - Conexión a Odoo
    │   └── 📄 calculators.py           # Funciones de cálculo financiero
    │
    ├── 📁 auth/                        # Módulo de Autenticación
    │   ├── 📄 __init__.py              # Blueprint auth_bp
    │   └── 📄 routes.py                # Rutas: /api/v1/auth/*
    │
    ├── 📁 collections/                 # Módulo de Cobranzas
    │   ├── 📄 __init__.py              # Blueprint collections_bp
    │   ├── 📄 routes.py                # Rutas: /api/v1/collections/*
    │   └── 📄 services.py              # CollectionsService - Lógica de negocio
    │
    └── 📁 treasury/                    # Módulo de Tesorería
        ├── 📄 __init__.py              # Blueprint treasury_bp
        ├── 📄 routes.py                # Rutas: /api/v1/treasury/*
        └── 📄 services.py              # TreasuryService (placeholder)
```

## 📊 Componentes por Capa

### Capa de Configuración
- `config.py` - Clases de configuración para diferentes entornos
- `.env.desarrollo` - Variables de entorno para desarrollo
- `.env.produccion` - Variables de entorno para producción

### Capa de Aplicación
- `run.py` - Inicialización de la aplicación
- `app/__init__.py` - Factory pattern y registro de blueprints

### Capa Core (Compartida)
- `app/core/odoo.py` - Repositorio para acceso a Odoo (Patrón Repository)
- `app/core/calculators.py` - Utilidades para cálculos financieros

### Capa de Módulos (Blueprints)

#### 🔐 Módulo Auth
```
app/auth/
├── __init__.py    → Define el Blueprint 'auth_bp'
└── routes.py      → Endpoints de autenticación
                     - POST /api/v1/auth/login
                     - GET /api/v1/auth/status
```

#### 💰 Módulo Collections (Cobranzas)
```
app/collections/
├── __init__.py    → Define el Blueprint 'collections_bp'
├── services.py    → CollectionsService con lógica de negocio
│                    - get_report_lines()
│                    - get_report_internacional()
│                    - filter_nacional()
│                    - filter_internacional()
└── routes.py      → Endpoints de cobranzas
                     - GET /api/v1/collections/report/account12
                     - GET /api/v1/collections/report/national
                     - GET /api/v1/collections/report/international
                     - GET /api/v1/collections/status
```

#### 🏦 Módulo Treasury (Tesorería)
```
app/treasury/
├── __init__.py    → Define el Blueprint 'treasury_bp'
├── services.py    → TreasuryService (placeholder)
└── routes.py      → Endpoints de tesorería
                     - GET /api/v1/treasury/report/account42
                     - GET /api/v1/treasury/status
```

## 🔄 Flujo de Datos

```
1. Cliente HTTP
   ↓
2. Flask (run.py → create_app)
   ↓
3. Blueprint Routes (routes.py)
   ↓
4. Service Layer (services.py)
   ↓
5. OdooRepository (odoo.py)
   ↓
6. Odoo (XML-RPC)
```

## 🎯 Patrones de Diseño Utilizados

| Patrón | Archivo | Propósito |
|--------|---------|-----------|
| **Factory** | `app/__init__.py` | Crear instancias de app con diferentes configs |
| **Blueprint** | `app/*/___init__.py` | Modularizar la aplicación |
| **Repository** | `app/core/odoo.py` | Abstraer el acceso a datos de Odoo |
| **Service Layer** | `app/*/services.py` | Separar lógica de negocio de rutas |

## 📝 Archivos que Debes Crear Manualmente

⚠️ **IMPORTANTE:** Estos archivos NO están en el repositorio por seguridad:

1. **`.env.desarrollo`** - En la raíz del proyecto
2. **`.env.produccion`** - En la raíz del proyecto
3. **`venv/`** - Crear con: `python -m venv venv`

Ver `INSTRUCCIONES_INICIO_RAPIDO.md` para detalles.

## 🔑 Archivos Clave

| Archivo | Descripción | Líneas Aprox. |
|---------|-------------|---------------|
| `config.py` | Configuraciones de entornos | ~100 |
| `app/__init__.py` | Factory y registro de blueprints | ~70 |
| `app/core/odoo.py` | Repositorio de Odoo | ~180 |
| `app/core/calculators.py` | Funciones de cálculo | ~180 |
| `app/collections/services.py` | Lógica de cobranzas | ~450 |
| `app/collections/routes.py` | Endpoints de cobranzas | ~250 |

## 📊 Estadísticas del Proyecto

- **Total de Módulos:** 3 (auth, collections, treasury)
- **Total de Endpoints:** ~10
- **Líneas de Código:** ~1,500+
- **Archivos Python:** 15
- **Archivos de Documentación:** 4

## 🚀 Comandos Útiles

```bash
# Ver estructura de archivos
tree /F    # Windows
tree       # Linux/Mac

# Contar líneas de código
find . -name "*.py" | xargs wc -l    # Linux/Mac

# Activar entorno virtual
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac

# Ejecutar aplicación
python run.py                # Desarrollo
python run.py production     # Producción
```

## 📚 Referencias

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Blueprints](https://flask.palletsprojects.com/en/latest/blueprints/)
- [Odoo XML-RPC API](https://www.odoo.com/documentation/master/developer/misc/api/odoo.html)

---

**Última actualización:** Noviembre 2025

