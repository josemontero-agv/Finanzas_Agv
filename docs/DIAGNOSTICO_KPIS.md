# 🔍 Diagnóstico: KPIs No Se Calculan

## ✅ Cambios Aplicados

1. **Mejorado `loadStats()` en frontend:**
   - Filtrado correcto de parámetros vacíos
   - Logging detallado en consola
   - Manejo de errores mejorado
   - Valores por defecto si falla

2. **Mejorado endpoint `/report/account12/stats`:**
   - Logging detallado en servidor
   - Debug de filtros recibidos
   - Debug de stats calculados

---

## 🔧 Pasos para Diagnosticar

### 1. **Abrir Consola del Navegador (F12)**

Busca estos mensajes:
```
[DEBUG] Cargando stats con filtros: {...}
[DEBUG] Respuesta stats: {...}
[DEBUG] Stats actualizados: {...}
```

**Si NO ves estos mensajes:**
- El método `loadStats()` no se está llamando
- Verifica que `init()` llame a `loadStats()`

**Si ves ERROR:**
- Copia el mensaje de error completo
- Verifica la URL del endpoint
- Verifica que el servidor esté corriendo

### 2. **Verificar Endpoint Directamente**

Abre en el navegador:
```
http://localhost:5000/api/v1/collections/report/account12/stats
```

**Deberías ver JSON:**
```json
{
  "success": true,
  "data": {
    "total_count": 1234,
    "total_amount": 500000.00,
    "pending_amount": 250000.00,
    "overdue_amount": 50000.00,
    "paid_amount": 250000.00
  }
}
```

**Si ves error:**
- Revisa los logs del servidor Flask
- Verifica conexión a Odoo
- Verifica credenciales

### 3. **Verificar Logs del Servidor**

En la terminal donde corre Flask, busca:
```
[DEBUG] report_account12_stats llamado
[DEBUG] Filtros recibidos: ...
[INFO] Calculando estadísticas agregadas...
[OK] Stats calculados: {...}
```

**Si ves ERROR:**
- Copia el traceback completo
- Verifica que Odoo esté conectado
- Verifica que el método `get_aggregated_stats` funcione

### 4. **Verificar Network Tab (F12 → Network)**

1. Filtra por "XHR" o "Fetch"
2. Busca request a `/api/v1/collections/report/account12/stats`
3. Verifica:
   - **Status:** 200 ✅
   - **Response:** JSON con `success: true`
   - **Timing:** < 2s

**Si Status es 500:**
- Hay un error en el servidor
- Revisa logs del servidor

**Si Status es 404:**
- El endpoint no existe
- Verifica la ruta en `routes.py`

---

## 🐛 Problemas Comunes

### Problema 1: "Stats siempre muestran 0"

**Causa:** El método `get_aggregated_stats` está retornando ceros.

**Solución:**
1. Verifica en logs del servidor si hay errores
2. Verifica que haya datos en Odoo con esos filtros
3. Prueba el endpoint directamente sin filtros

### Problema 2: "Error en consola: Network Error"

**Causa:** El servidor no está respondiendo o hay CORS.

**Solución:**
1. Verifica que Flask esté corriendo
2. Verifica la URL del endpoint
3. Verifica que no haya errores en el servidor

### Problema 3: "Stats no se actualizan al cambiar filtros"

**Causa:** `loadStats()` no se llama cuando se aplican filtros.

**Solución:**
1. Verifica que `applyFilters()` llame a `loadStats()`
2. Verifica en consola si se hace el request
3. Verifica que los filtros se pasen correctamente

### Problema 4: "Stats se calculan pero no se muestran"

**Causa:** Alpine.js no está actualizando la vista.

**Solución:**
1. Verifica que `x-text` esté en los elementos
2. Verifica que `stats` esté en el scope de Alpine
3. Verifica en consola que `this.stats` tenga valores

---

## 🧪 Test Manual

### Test 1: Endpoint Directo
```bash
# En navegador o con curl
curl http://localhost:5000/api/v1/collections/report/account12/stats
```

**Esperado:** JSON con stats

### Test 2: Con Filtros
```bash
curl "http://localhost:5000/api/v1/collections/report/account12/stats?date_from=2024-01-01&date_to=2024-12-31"
```

**Esperado:** JSON con stats filtrados

### Test 3: Desde Consola del Navegador
```javascript
// En la consola del navegador (F12)
const response = await fetch('/api/v1/collections/report/account12/stats');
const data = await response.json();
console.log(data);
```

**Esperado:** Objeto con `success: true` y `data` con stats

---

## 📊 Verificación de Datos

### Verificar que hay datos en Odoo:
1. Abre el endpoint de rows:
   ```
   http://localhost:5000/api/v1/collections/report/account12/rows?page=1
   ```
2. Si hay filas, debería haber stats
3. Si no hay filas, los stats serán 0 (correcto)

### Verificar que los cálculos sean correctos:
1. Compara `total_count` con el número de filas
2. Compara `total_amount` con la suma de `amount_total` de las filas
3. Compara `pending_amount` con la suma de `amount_residual_with_retention`

---

## 🔧 Solución Rápida

Si después de revisar todo aún no funciona, prueba esto en la consola del navegador:

```javascript
// Forzar carga de stats
const controller = Alpine.$data(document.querySelector('[x-data]'));
await controller.loadStats();
console.log('Stats:', controller.stats);
```

Si esto funciona, el problema está en el timing de la carga inicial.

---

## 📝 Checklist

- [ ] ¿El endpoint `/stats` responde cuando lo abres directamente?
- [ ] ¿Los logs del servidor muestran que se llama el endpoint?
- [ ] ¿Los logs del servidor muestran stats calculados?
- [ ] ¿La consola del navegador muestra el request a `/stats`?
- [ ] ¿La consola del navegador muestra la respuesta?
- [ ] ¿Alpine.js está actualizando la vista?
- [ ] ¿Los valores de `stats` están en el objeto del controller?

---

**Si después de revisar todo esto aún no funciona, comparte:**
1. Logs de la consola del navegador
2. Logs del servidor Flask
3. Respuesta del endpoint cuando lo abres directamente

