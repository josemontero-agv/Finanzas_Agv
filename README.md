# Finanzas AGV - API REST

API REST para gestión financiera - Cobranzas y Tesorería

## 📋 Descripción

Aplicación Flask con arquitectura API-First y monolito modular para la gestión de:
- **Cobranzas (Collections)**: Reportes de cuentas por cobrar, nacionales e internacionales
- **Tesorería (Treasury)**: Reportes de flujo de caja y tesorería (en desarrollo)
- **Autenticación**: Login de usuarios contra Odoo

## 🏗️ Arquitectura

- **Patrón Factory**: `create_app()` para diferentes entornos
- **Blueprints modulares**: auth, collections, treasury
- **Capa de servicios**: Lógica de negocio separada
- **Patrón Repository**: Abstracción del acceso a Odoo
- **API-First**: Todos los endpoints devuelven JSON

## 📁 Estructura del Proyecto

```
Finanzas_Agv/
│
├── app/
│   ├── __init__.py              # Factory pattern
│   ├── core/
│   │   ├── odoo.py              # OdooRepository
│   │   └── calculators.py       # Utilidades financieras
│   │
│   ├── auth/
│   │   ├── __init__.py          # Blueprint auth
│   │   └── routes.py            # Endpoints de autenticación
│   │
│   ├── collections/
│   │   ├── __init__.py          # Blueprint collections
│   │   ├── routes.py            # Endpoints de cobranzas
│   │   └── services.py          # CollectionsService
│   │
│   └── treasury/
│       ├── __init__.py          # Blueprint treasury
│       ├── routes.py            # Endpoints de tesorería
│       └── services.py          # TreasuryService (placeholder)
│
├── config.py                    # Configuraciones (Dev/Prod/Test)
├── run.py                       # Punto de entrada
├── requirements.txt             # Dependencias
├── .env.desarrollo              # Variables de desarrollo (NO SUBIR A GIT)
├── .env.produccion              # Variables de producción (NO SUBIR A GIT)
└── .gitignore                   # Archivos ignorados por Git
```

## 🚀 Instalación

### 1. Crear entorno virtual

```bash
cd Finanzas_Agv
python -m venv venv
```

### 2. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

## ⚙️ Configuración de Variables de Entorno

### IMPORTANTE: Archivos .env

Debes crear **DOS archivos** en la raíz del proyecto:

#### 📄 `.env.desarrollo`

```bash
# Configuración de desarrollo para Finanzas AGV
# IMPORTANTE: NO SUBIR ESTE ARCHIVO A GIT

# Flask
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Odoo Connection
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database_name
ODOO_USER=your_username
ODOO_PASSWORD=your_password
```

#### 📄 `.env.produccion`

```bash
# Configuración de producción para Finanzas AGV
# IMPORTANTE: NO SUBIR ESTE ARCHIVO A GIT

# Flask
SECRET_KEY=production-secret-key-must-be-strong
FLASK_ENV=production
FLASK_DEBUG=False

# Odoo Connection
ODOO_URL=https://your-odoo-production.com
ODOO_DB=production_database
ODOO_USER=production_user
ODOO_PASSWORD=production_password
```

### 🔒 Seguridad

- **NUNCA** subas los archivos `.env.*` a Git
- Ya están incluidos en `.gitignore`
- Usa credenciales diferentes para desarrollo y producción
- Genera un `SECRET_KEY` fuerte para producción

## 🎯 Ejecución

### Modo Desarrollo (por defecto)

```bash
python run.py
```

o explícitamente:

```bash
python run.py development
```

### Modo Producción

```bash
python run.py production
```

### Modo Testing

```bash
python run.py testing
```

La aplicación se ejecutará en: `http://localhost:5000`

## 📡 Endpoints Disponibles

### Raíz
- **GET** `/` - Información general de la API

### Autenticación (`/api/v1/auth`)
- **POST** `/api/v1/auth/login` - Login de usuario
- **GET** `/api/v1/auth/status` - Estado del módulo

### Cobranzas (`/api/v1/collections`)
- **GET** `/api/v1/collections/report/account12` - Reporte general CxC
- **GET** `/api/v1/collections/report/national` - Reporte nacional
- **GET** `/api/v1/collections/report/international` - Reporte internacional
- **GET** `/api/v1/collections/status` - Estado del módulo

### Tesorería (`/api/v1/treasury`)
- **GET** `/api/v1/treasury/report/account42` - Reporte Cta 42 (placeholder)
- **GET** `/api/v1/treasury/status` - Estado del módulo

## 📝 Ejemplos de Uso

### Login

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario",
    "password": "contraseña"
  }'
```

### Reporte General de Cobranzas

```bash
curl "http://localhost:5000/api/v1/collections/report/account12?date_from=2024-01-01&date_to=2024-12-31"
```

### Reporte Nacional

```bash
curl "http://localhost:5000/api/v1/collections/report/national?date_from=2024-01-01"
```

### Reporte Internacional

```bash
curl "http://localhost:5000/api/v1/collections/report/international?date_from=2024-01-01"
```

## 🔧 Parámetros de Query para Reportes de Cobranzas

### `/report/account12` (General)
- `date_from` - Fecha inicial (YYYY-MM-DD)
- `date_to` - Fecha final (YYYY-MM-DD)
- `customer` - Nombre del cliente
- `account_codes` - Códigos de cuenta (separados por coma)
- `sales_channel_id` - ID del canal de ventas
- `doc_type_id` - ID del tipo de documento
- `limit` - Límite de registros (default: 10000)

### `/report/national` (Nacional)
- `date_from` - Fecha inicial
- `date_to` - Fecha final
- `customer` - Nombre del cliente
- `account_codes` - Códigos de cuenta
- `limit` - Límite de registros

### `/report/international` (Internacional)
- `date_from` - Fecha inicial
- `date_to` - Fecha final
- `customer` - Nombre del cliente
- `payment_state` - Estado de pago
- `limit` - Límite de registros

## 🧪 Testing

```bash
# Ejecutar en modo testing
python run.py testing

# O con pytest (si está instalado)
pytest
```

## 📦 Producción con Gunicorn

Para producción real, usa Gunicorn (ya incluido en requirements.txt):

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app('production')"
```

## 🛠️ Tecnologías Utilizadas

- **Flask 3.0.0** - Framework web
- **Python 3.x** - Lenguaje de programación
- **XML-RPC** - Comunicación con Odoo
- **python-dotenv** - Gestión de variables de entorno
- **Gunicorn** - Servidor WSGI para producción

## 📚 Dependencias

Ver `requirements.txt` para la lista completa de dependencias.

## 🤝 Contribución

1. Crear rama para nueva feature: `git checkout -b feature/nueva-funcionalidad`
2. Hacer commit de cambios: `git commit -m "Añadir nueva funcionalidad"`
3. Push a la rama: `git push origin feature/nueva-funcionalidad`
4. Crear Pull Request

## 📄 Licencia

Proyecto interno de AGV - Todos los derechos reservados

## 📞 Contacto

Para soporte o consultas, contactar al equipo de desarrollo de AGV.

---

**Nota:** Esta es una aplicación API-First. NO sirve HTML. Todos los endpoints devuelven JSON.
