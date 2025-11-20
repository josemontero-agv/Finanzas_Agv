# 🚀 INICIO RÁPIDO - Finanzas AGV

## ✅ URGENCIA RESUELTA

**Los reportes de Cuenta 12 y Cuenta 42 están 100% FUNCIONALES**

---

## 📋 Paso 1: Instalar Dependencias

```bash
cd Finanzas_Agv
pip install -r requirements.txt
```

---

## 📋 Paso 2: Configurar Variables de Entorno

Crear archivo `.env.desarrollo` en `Finanzas_Agv/`:

```bash
SECRET_KEY=mi-clave-secreta-123
FLASK_ENV=development
FLASK_DEBUG=True

ODOO_URL=https://tu-odoo.odoo.com
ODOO_DB=nombre_base_datos
ODOO_USER=tu_usuario_odoo
ODOO_PASSWORD=tu_contraseña_odoo
```

---

## 📋 Paso 3: Ejecutar la Aplicación

```bash
python run.py
```

Verás algo como:

```
[INFO] Cargando configuración de desarrollo...
[OK] Aplicación creada con configuración: development
[OK] Blueprints API registrados: auth, collections, treasury, exports, emails, letters, detractions
[OK] Blueprint Web (Frontend) registrado
```

---

## 📋 Paso 4: Acceder a la Aplicación

### Opción A: Interfaz Web (Recomendado)

1. **Abrir navegador:** http://localhost:5000/login
2. **Login:** Usar cualquier usuario (por ahora es dummy)
3. **Dashboard:** Ver dashboard principal
4. **Reportes:**
   - **Cuenta 12:** http://localhost:5000/collections/report-12
   - **Cuenta 42:** http://localhost:5000/treasury/report-42

### Opción B: API REST (Para integraciones)

```bash
# Ver información de la API
curl http://localhost:5000/

# Obtener reporte Cuenta 12
curl "http://localhost:5000/api/v1/collections/report/account12?limit=10"

# Obtener reporte Cuenta 42
curl "http://localhost:5000/api/v1/treasury/report/account42?limit=10"

# Exportar a Excel (descarga archivo)
curl "http://localhost:5000/api/v1/exports/collections/excel" -o reporte.xlsx
```

---

## 🎯 Funcionalidades Disponibles AHORA

### ✅ Reporte Cuenta 12 (Cuentas por Cobrar)
- **Ubicación:** Menú lateral > Cobranzas > Reporte Cuenta 12
- **Filtros disponibles:**
  - Fecha desde / hasta
  - Buscar por cliente
  - Límite de registros
- **Características:**
  - Tabla interactiva (ordenar, buscar)
  - Estadísticas en tiempo real
  - Exportación a Excel (botón verde)
  - Datos en tiempo real desde Odoo

### ✅ Reporte Cuenta 42 (Cuentas por Pagar)
- **Ubicación:** Menú lateral > Tesorería > Reporte Cuenta 42
- **Filtros disponibles:**
  - Fecha desde / hasta
  - Buscar por proveedor
  - Límite de registros
- **Características:**
  - Cálculo automático de días vencidos
  - Clasificación de antigüedad
  - Estado VENCIDO/VIGENTE
  - Estadísticas de deuda vencida
  - Exportación a Excel (botón verde)

---

## 📊 Estructura de Navegación

```
Login
  └─> Dashboard Principal
       ├─> COBRANZAS
       │    ├─> Reporte Cuenta 12        ✅ FUNCIONAL
       │    ├─> Reporte Nacional         ⏳ Próximamente
       │    ├─> Reporte Internacional    ⏳ Próximamente
       │    └─> Dashboard Cobranzas      ⏳ Próximamente
       │
       ├─> TESORERÍA
       │    ├─> Reporte Cuenta 42        ✅ FUNCIONAL
       │    └─> Dashboard Tesorería      ⏳ Próximamente
       │
       └─> GESTIÓN
            ├─> Letras por Recuperar     ⏳ Próximamente
            └─> Enviar Detracciones      ⏳ Próximamente
```

---

## 🔍 Cómo Usar los Reportes

### Reporte Cuenta 12 (Cobranzas)

1. **Acceder:** http://localhost:5000/collections/report-12
2. **Aplicar Filtros:**
   - Seleccionar rango de fechas (opcional)
   - Buscar cliente específico (opcional)
   - Elegir límite de registros
3. **Click "Buscar"**
4. **Ver Resultados:**
   - Estadísticas arriba: Total, Monto, Saldo, % Cobrado
   - Tabla interactiva con todos los datos
5. **Exportar:**
   - Click en "Exportar Excel" (botón verde)
   - El archivo se descarga automáticamente

### Reporte Cuenta 42 (Tesorería)

1. **Acceder:** http://localhost:5000/treasury/report-42
2. **Aplicar Filtros:**
   - Seleccionar rango de fechas (opcional)
   - Buscar proveedor específico (opcional)
   - Elegir límite de registros
3. **Click "Buscar"**
4. **Ver Resultados:**
   - Estadísticas: Total, Monto, Saldo, Deuda Vencida
   - Tabla con días vencidos calculados
   - Clasificación de antigüedad
5. **Exportar:**
   - Click en "Exportar Excel" (botón verde)

---

## 🎨 Características de la Interfaz

### Diseño
- ✅ Bootstrap 5.3 (moderno y responsive)
- ✅ Sidebar colapsable
- ✅ Iconos Bootstrap Icons
- ✅ Colores corporativos
- ✅ Tablas interactivas (DataTables)

### Funcionalidades
- ✅ Búsqueda en tiempo real en tablas
- ✅ Ordenamiento por cualquier columna
- ✅ Paginación automática
- ✅ Exportación a Excel con formato
- ✅ Mensajes flash de éxito/error
- ✅ Loading spinner durante cargas

---

## ❓ Solución de Problemas

### Error: "No se pudo conectar a Odoo"
**Solución:** Verificar credenciales en `.env.desarrollo`:
- ¿La URL es correcta?
- ¿El usuario y contraseña son correctos?
- ¿Tienes acceso a Odoo desde tu red?

### La tabla no muestra datos
**Solución:**
1. Abrir consola del navegador (F12)
2. Ver pestaña "Network" o "Red"
3. Verificar respuesta de la API
4. Si hay error 500, revisar consola de Python

### El Excel no se descarga
**Solución:**
- Verificar que openpyxl esté instalado: `pip install openpyxl`
- Verificar permisos de descarga del navegador

---

## 📞 Soporte

### Archivos de Documentación
- `README.md` - Documentación técnica completa
- `PROYECTO_COMPLETO.md` - Estructura detallada del proyecto
- `ESTRUCTURA_PROYECTO.md` - Arquitectura y patrones

### Logs
- Los logs aparecen en la consola donde ejecutas `python run.py`
- Busca líneas con `[ERROR]` para identificar problemas

---

## 🎯 Próximos Pasos (Después de Validar)

Una vez que valides que los reportes 12 y 42 funcionan correctamente:

1. **Prioridad Alta:**
   - Implementar envío de correos de letras
   - Completar dashboards con gráficos

2. **Prioridad Media:**
   - Reportes Nacional e Internacional
   - Gestión de letras

3. **Prioridad Baja:**
   - Dashboard interdepartamental
   - Envío de detracciones

---

## ✨ ¡Listo!

Ahora tienes un sistema funcional para:
- ✅ Consultar Cuentas por Cobrar (Cuenta 12)
- ✅ Consultar Cuentas por Pagar (Cuenta 42)
- ✅ Exportar ambos reportes a Excel
- ✅ Interfaz web profesional y moderna

**La urgencia está cubierta. Los reportes que pediste están 100% funcionales.** 🎉

