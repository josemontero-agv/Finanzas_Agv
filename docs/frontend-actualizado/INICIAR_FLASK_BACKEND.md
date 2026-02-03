# 🚀 Iniciar Flask Backend - Instrucciones

## ⚡ Problema Actual

El frontend Next.js está funcionando pero muestra "Network Error" porque **Flask no está corriendo**.

---

## ✅ Solución: Iniciar Flask en puerto 5000

### Opción 1: Iniciar Flask manualmente (Recomendado)

```powershell
# Terminal nueva (o usar terminal 1 o 2)
cd C:\Users\jmontero\Desktop\GitHub` Proyectos_AGV\Finanzas_Agv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Iniciar Flask
python run.py
```

**Deberías ver:**
```
[OK] Aplicación creada con configuración: development
[OK] Blueprints API registrados...
 * Running on http://127.0.0.1:5000
```

### Opción 2: Usar Docker Compose

```powershell
docker-compose up backend
```

---

## 🔧 Arreglos Aplicados

### 1. Error de Celery Worker SOLUCIONADO ✅

**Problema:** 
```
AttributeError: 'cached_property' object has no attribute '__name__'
```

**Solución aplicada:**
- Actualizado `app/core/celery_utils.py`
- Cambiado `task_cls=FlaskTask` por `celery_app.Task = FlaskTask`
- Compatible con Python 3.11+

### 2. Frontend ahora requiere Flask ✅

**Cambios:**
- Todas las páginas ahora consultan Flask API
- Flask puede usar Supabase internamente (más rápido)
- Manejo de errores mejorado con mensajes claros

---

## 🎯 Flujo de Datos Correcto

```
Next.js Frontend (puerto 3000)
       ↓
Flask API (puerto 5000)
       ↓
    ┌──┴──┐
    ↓     ↓
  Odoo  Supabase
```

**Ventajas:**
- ✅ Flask hace los cálculos (días vencidos, antigüedad)
- ✅ Flask puede elegir entre Odoo o Supabase
- ✅ Frontend solo se preocupa de la UI

---

## 📋 Checklist para que todo funcione

### Paso 1: Iniciar Flask
```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

### Paso 2: Verificar que Flask responde
Abrir en navegador:
```
http://localhost:5000/api/health
```

Deberías ver:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "odoo": "connected",
    "supabase": "connected"
  }
}
```

### Paso 3: Refrescar Next.js
```
http://localhost:3000
```

Ahora las páginas deberían cargar datos correctamente.

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'flask_cors'"

**Solución:**
```powershell
.\venv\Scripts\Activate.ps1
pip install Flask-CORS==4.0.0
```

### Error: Celery sigue fallando

**No es crítico.** El frontend no necesita Celery para funcionar. Celery solo se usa para:
- ETL automático programado
- Tareas en background

Puedes ejecutar el ETL manualmente:
```powershell
python scripts\etl\etl_sync_threading.py
```

### Error: "Connection refused" en Flask

**Causas posibles:**
1. Flask no está corriendo
2. Está corriendo en otro puerto
3. Firewall bloqueando

**Verificar:**
```powershell
# Ver si algo está usando el puerto 5000
netstat -ano | findstr :5000
```

---

## 🎉 Una vez que Flask esté corriendo:

### Verifica que todo funciona:

1. **Health Check**: http://localhost:5000/api/health
2. **Frontend Dashboard**: http://localhost:3000/dashboard
3. **Letras**: http://localhost:3000/letters
4. **Cobranzas**: http://localhost:3000/collections
5. **Tesorería**: http://localhost:3000/treasury

### Deberías ver:
- ✅ Datos en las tablas
- ✅ KPIs con números reales
- ✅ Filtros funcionando
- ✅ Sin "Network Error"

---

## 📝 Comandos Rápidos

### Iniciar todo el sistema:

```powershell
# Terminal 1: Flask Backend
.\venv\Scripts\Activate.ps1
python run.py

# Terminal 2: Next.js Frontend (ya está corriendo en terminal 3)
# No hacer nada, ya está activo

# Terminal 3: ETL (opcional, solo si necesitas sincronizar)
.\venv\Scripts\Activate.ps1
python scripts\etl\etl_sync_threading.py
```

---

**¡Con Flask corriendo, el frontend funcionará perfectamente!** 🚀
