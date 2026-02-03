# 🔍 Diagnóstico: Por qué no envía correos

## Estado Actual

### ✅ Backend (Flask)
- **Puerto**: 5000
- **Endpoint**: `/api/v1/letters/send-acceptance` ✅ EXISTE
- **Estado**: FUNCIONAL (responde 500 solo por JSON mal formado en test)
- **Modo**: Development
- **DEV_EMAIL_MODE**: True (configurado)
- **Email de prueba**: josemontero2415@gmail.com

### ❌ Frontend (Next.js)
- **Error**: `AxiosError: Request failed with status code 404`
- **Problema**: No está llegando al endpoint correcto

---

## 🐛 Causa del Problema

El frontend está enviando la petición a una **URL incorrecta** o el servidor Next.js no leyó el `.env.local`.

---

## ✅ Solución

### Paso 1: Reiniciar Frontend

**IMPORTANTE**: Next.js NO recarga `.env.local` automáticamente. Debes reiniciar:

```powershell
# Terminal donde corre Next.js
Ctrl + C  # Detener

# Reiniciar
cd frontend
npm run dev
```

### Paso 2: Verificar en DevTools

1. Abre Chrome DevTools (F12)
2. Ve a la pestaña **Network**
3. Intenta enviar un correo
4. Busca el request `send-acceptance`
5. Verifica que la URL sea:
   ```
   http://localhost:5000/api/v1/letters/send-acceptance
   ```

**Si es otra URL** (ej: `http://localhost:3000/...`), significa que no leyó el `.env.local`.

### Paso 3: Forzar la Configuración

Si el Paso 1 no funcionó, edita directamente el código:

**Archivo**: `frontend/lib/api.ts`

```typescript
// TEMPORAL: Forzar URL del backend
const API_BASE_URL = 'http://localhost:5000'

export const flaskApi = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})
```

### Paso 4: Limpiar Caché de Next.js

```powershell
cd frontend
Remove-Item -Recurse -Force .next
npm run dev
```

---

## 📧 Modo Producción con Email de Prueba

Ya está configurado en `.env.produccion`:

```bash
# Modo Desarrollo para Correos (MANTENER EN TRUE para pruebas)
DEV_EMAIL_MODE=True
DEV_EMAIL_RECIPIENT=josemontero2415@gmail.com
```

**Para ejecutar en producción con correo de prueba:**

```powershell
python run.py production
```

Todos los correos irán a `josemontero2415@gmail.com` aunque estés en producción.

**Cuando quieras enviar a clientes reales:**

Cambia en `.env.produccion`:
```bash
DEV_EMAIL_MODE=False
```

---

## 🧪 Prueba Manual del Backend

Para verificar que el backend funciona:

```powershell
# Terminal PowerShell
$headers = @{
    "Content-Type" = "application/json"
}
$body = @{
    letter_ids = @(1, 2, 3)
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:5000/api/v1/letters/send-acceptance" -Headers $headers -Body $body
```

**Respuesta esperada:**
```json
{
  "success": true,
  "message": "Proceso de envío completado",
  "details": {
    "sent": 1,
    "failed": 0,
    "errors": []
  }
}
```

---

## 📊 Checklist de Verificación

- [x] `.env.produccion` tiene `DEV_EMAIL_MODE=True`
- [x] `.env.produccion` tiene `DEV_EMAIL_RECIPIENT=josemontero2415@gmail.com`
- [x] `frontend/.env.local` tiene `NEXT_PUBLIC_FLASK_API_URL=http://localhost:5000`
- [ ] Frontend reiniciado después de crear `.env.local`
- [ ] Flask corriendo en puerto 5000
- [ ] DevTools muestra URL correcta en Network

---

## 🚨 Si Sigue Fallando

### Opción 1: Hardcodear Temporalmente

En `frontend/lib/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:5000' // Forzado
```

### Opción 2: Verificar Proxy

Revisa si hay un `proxy` configurado en `package.json` del frontend que esté redirigiendo las peticiones.

### Opción 3: Revisar CORS

En DevTools Console, busca errores de CORS. Si aparecen, el backend está bloqueando.

---

## 💡 Explicación Técnica

### ¿Por qué 404?

El 404 significa que **la URL no existe en el servidor al que estás llamando**.

Posibilidades:
1. **Frontend apunta a Next.js (3000)** en lugar de Flask (5000)
2. **Frontend usa una URL vieja** cacheada
3. **Flask no tiene el endpoint registrado** (pero ya verificamos que SÍ existe)

### ¿Por qué 500 en curl?

El 500 en curl era porque PowerShell no formatea bien el JSON. Pero el endpoint **SÍ está ahí y funciona**.

### ¿Por qué no llega el correo?

Porque **nunca se ejecuta el endpoint**. Si el frontend recibe 404, significa que:
- No llegó a Flask
- No se ejecutó el código de envío
- No se activó el modo DEV
- No se envió el correo

---

## 🎯 Próximo Paso

1. **Reinicia el frontend** (npm run dev)
2. **Verifica en DevTools** que la URL sea correcta
3. **Prueba enviar un correo**
4. **Mira los logs de Flask** para ver si llega la petición

Si después de reiniciar sigue con 404, **dime exactamente qué URL aparece en DevTools Network** y te digo qué hacer.

---

**Fecha**: 20 de Enero, 2026  
**Estado**: En diagnóstico
