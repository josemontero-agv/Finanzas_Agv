# ⚡ EJECUTAR AHORA - Instrucciones Inmediatas

## 🎯 Para ver el frontend funcionando en 2 minutos:

### Paso 1: Ejecutar ETL (Solo primera vez)
```powershell
.\venv\Scripts\Activate.ps1
python scripts\etl\etl_sync_threading.py
```

**Tiempo estimado**: 2-5 minutos  
**Qué hace**: Sincroniza facturas, letras y clientes desde Odoo a Supabase

### Paso 2: El frontend ya está corriendo
Si ves esto en la terminal 3, ya está listo:
```
✓ Ready in 2.5s
Local: http://localhost:3000
```

### Paso 3: Abrir en el navegador
```
http://localhost:3000/diagnostics
```

Esta página te dirá si todo está bien.

---

## 🔍 Qué verás:

### Si el ETL ya corrió:
- ✅ Checkmarks verdes en todas las tablas
- ✅ Números de registros (ej: "1,234 registros")
- ✅ Las páginas de Letras, Cobranzas y Tesorería funcionarán

### Si el ETL NO ha corrido:
- ⚠️ Alertas amarillas "0 registros"
- ⚠️ Instrucciones de cómo ejecutar el ETL
- ⚠️ Las páginas dirán "No hay datos disponibles"

---

## 🚨 Si ves "Network Error":

### Solución Inmediata:
El frontend ahora está configurado para **NO depender de Flask**.

1. Refresca la página (F5)
2. Ve a http://localhost:3000/diagnostics
3. Verifica que Supabase tenga datos (checkmarks verdes)

### Si Supabase muestra 0 registros:
```powershell
# Ejecuta el ETL
.\venv\Scripts\Activate.ps1
python scripts\etl\etl_sync_threading.py
```

---

## 📋 Checklist Rápido:

- [ ] Frontend corriendo en terminal 3 (puerto 3000)
- [ ] ETL ejecutado al menos una vez
- [ ] Página de diagnóstico muestra checkmarks verdes
- [ ] Puedes navegar entre Letras, Cobranzas, Tesorería

---

## 🎉 Una vez que funcione:

### Navega por los módulos:
1. **Dashboard**: http://localhost:3000/dashboard
2. **Letras**: http://localhost:3000/letters
3. **Cobranzas**: http://localhost:3000/collections
4. **Tesorería**: http://localhost:3000/treasury

### Características que verás:
- ✅ Sidebar moderno con gradientes
- ✅ Tablas profesionales con Shadcn
- ✅ KPI Cards con iconos
- ✅ Filtros funcionales
- ✅ Paginación
- ✅ Responsive design

---

## 🆘 Si nada funciona:

```powershell
# 1. Detener el frontend (Ctrl+C en terminal 3)

# 2. Reinstalar dependencias
cd frontend
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install

# 3. Reiniciar
npm run dev

# 4. Abrir diagnóstico
start http://localhost:3000/diagnostics
```

---

## ✅ Comando Todo-en-Uno:

```powershell
# Ejecutar ETL + Iniciar Frontend
.\venv\Scripts\Activate.ps1
python scripts\etl\etl_sync_threading.py
cd frontend
npm run dev
```

**Luego abre**: http://localhost:3000/diagnostics

---

**¡El sistema está listo! Solo necesita datos del ETL.** 🚀
