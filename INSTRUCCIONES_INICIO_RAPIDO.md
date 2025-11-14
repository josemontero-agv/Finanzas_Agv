# 🚀 Inicio Rápido - Finanzas AGV

## Pasos para Ejecutar la Aplicación

### 1️⃣ Crear los Archivos de Variables de Entorno

Crea **DOS archivos** en la carpeta `Finanzas_Agv/`:

#### 📄 `.env.desarrollo`
```bash
# Configuración de desarrollo
SECRET_KEY=dev-secret-key-change-me
FLASK_ENV=development
FLASK_DEBUG=True

# Odoo Connection (REEMPLAZAR CON TUS CREDENCIALES)
ODOO_URL=https://tu-instancia-odoo.com
ODOO_DB=nombre_base_datos
ODOO_USER=tu_usuario
ODOO_PASSWORD=tu_contraseña
```

#### 📄 `.env.produccion`
```bash
# Configuración de producción
SECRET_KEY=production-secret-key-debe-ser-fuerte-y-unica
FLASK_ENV=production
FLASK_DEBUG=False

# Odoo Connection de PRODUCCIÓN (REEMPLAZAR CON CREDENCIALES DE PRODUCCIÓN)
ODOO_URL=https://tu-instancia-odoo-produccion.com
ODOO_DB=nombre_base_datos_produccion
ODOO_USER=usuario_produccion
ODOO_PASSWORD=contraseña_produccion
```

### 2️⃣ Crear y Activar Entorno Virtual

**Windows:**
```bash
cd Finanzas_Agv
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
cd Finanzas_Agv
python -m venv venv
source venv/bin/activate
```

### 3️⃣ Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4️⃣ Ejecutar la Aplicación

**Modo Desarrollo:**
```bash
python run.py
```

**Modo Producción:**
```bash
python run.py production
```

### 5️⃣ Probar la API

Abre tu navegador o Postman y visita:

```
http://localhost:5000/
```

Deberías ver la información de la API en formato JSON.

## 🎯 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información general de la API |
| POST | `/api/v1/auth/login` | Login de usuario |
| GET | `/api/v1/collections/report/account12` | Reporte general CxC |
| GET | `/api/v1/collections/report/national` | Reporte nacional |
| GET | `/api/v1/collections/report/international` | Reporte internacional |
| GET | `/api/v1/treasury/report/account42` | Reporte tesorería (placeholder) |

## 📝 Ejemplo de Petición con curl

### Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "tu_usuario", "password": "tu_contraseña"}'
```

### Reporte de Cobranzas
```bash
curl "http://localhost:5000/api/v1/collections/report/account12?date_from=2024-01-01&limit=10"
```

## 🐍 Ejemplo con Python

También puedes ejecutar el script de ejemplo incluido:

```bash
python EJEMPLO_USO.py
```

## ❓ Solución de Problemas

### Error: "Faltan credenciales de Odoo"
- Verifica que creaste los archivos `.env.desarrollo` o `.env.produccion`
- Asegúrate de que las variables ODOO_URL, ODOO_DB, ODOO_USER y ODOO_PASSWORD estén definidas

### Error: "No se pudo conectar a Odoo"
- Verifica que las credenciales de Odoo sean correctas
- Verifica que la URL de Odoo sea accesible
- Verifica tu conexión a internet

### El servidor no inicia
- Asegúrate de que el entorno virtual esté activado
- Verifica que todas las dependencias estén instaladas: `pip install -r requirements.txt`
- Verifica que el puerto 5000 no esté en uso

## 🎓 Próximos Pasos

1. ✅ Configurar credenciales reales de Odoo
2. ✅ Probar los endpoints con datos reales
3. ✅ Explorar los parámetros de filtrado disponibles
4. ✅ Integrar con tu aplicación frontend
5. ✅ Implementar autenticación JWT (opcional)

## 📚 Documentación Completa

Para más detalles, consulta el archivo `README.md` en la raíz del proyecto.

