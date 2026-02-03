# 🚀 Inicio Rápido - Frontend Next.js

## ⚡ Opción 1: Solo Frontend (Recomendado para empezar)

El frontend puede funcionar **independientemente** usando solo Supabase (sin necesidad de Flask).

### Pasos:

```bash
# 1. Ir al directorio frontend
cd frontend

# 2. Instalar dependencias (solo primera vez)
npm install

# 3. Iniciar el servidor de desarrollo
npm run dev
```

### ✅ Acceder:
- **URL**: http://localhost:3000
- **Dashboard**: http://localhost:3000/dashboard
- **Letras**: http://localhost:3000/letters
- **Cobranzas**: http://localhost:3000/collections
- **Tesorería**: http://localhost:3000/treasury

### 📊 Modo de Operación:
- Por defecto usa **Supabase directo** (ultra rápido)
- Los datos vienen de las tablas `fact_moves`, `fact_letters`, `dim_partners`
- Puedes cambiar a "Flask API" con el botón toggle (si Flask está corriendo)

---

## 🔧 Opción 2: Frontend + Backend (Completo)

Si quieres usar los cálculos avanzados (días vencidos, antigüedad, etc.):

### Terminal 1 - Backend Flask
```bash
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar Flask-CORS (si no lo has hecho)
pip install Flask-CORS==4.0.0

# Ejecutar Flask
python run.py
```

### Terminal 2 - Frontend Next.js
```bash
cd frontend
npm run dev
```

### ✅ Acceder:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

---

## 🐳 Opción 3: Docker Compose (Todo junto)

```bash
docker-compose up --build
```

Esto levanta:
- ✅ Backend Flask (puerto 5000)
- ✅ Frontend Next.js (puerto 3000)
- ✅ Redis (puerto 6379)
- ✅ Worker Celery

---

## 🔍 Verificar que todo funciona

### 1. Frontend cargando
Deberías ver en la terminal:

```
✓ Ready in 2.5s
○ Compiling / ...
✓ Compiled / in 1.2s
```

### 2. Abrir navegador
```
http://localhost:3000
```

### 3. Verificar conexión a Supabase
- Ve a `/collections` o `/treasury`
- Deberías ver datos de las tablas de Supabase
- Si ves "No hay datos disponibles", el ETL aún no ha sincronizado

### 4. Ejecutar ETL (si no hay datos)
```bash
# Activar venv
.\venv\Scripts\Activate.ps1

# Ejecutar sincronización
python scripts/etl/etl_sync_threading.py
```

---

## ❌ Troubleshooting

### Error: "Network Error" en todas las páginas

**Causa**: El frontend está intentando conectarse a Flask pero no está corriendo.

**Solución Rápida**: 
Las páginas ahora funcionan con **Supabase por defecto**. Solo asegúrate de que:
1. El archivo `frontend/.env.local` existe
2. Contiene las credenciales correctas de Supabase
3. El ETL ha sincronizado datos a Supabase

**Verificar .env.local**:
```bash
cd frontend
Get-Content .env.local
```

Debe contener:
```
NEXT_PUBLIC_SUPABASE_URL=https://qupyfyextppvlwlykmle.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Error: "No hay datos disponibles"

**Causa**: Las tablas de Supabase están vacías.

**Solución**: Ejecutar el ETL para sincronizar datos desde Odoo:
```bash
.\venv\Scripts\Activate.ps1
python scripts/etl/etl_sync_threading.py
```

### Error: Celery no inicia

**Causa**: Incompatibilidad de versiones (el error que viste en la terminal).

**Solución**: No es crítico para el frontend. El frontend funciona sin Celery.

---

## 🎯 Modo Recomendado para Desarrollo

### Para ver resultados inmediatos:

1. **Solo Frontend** (Opción 1)
   - Más rápido de iniciar
   - No depende de Flask
   - Usa Supabase directo

2. **Ejecutar ETL una vez** para tener datos
   ```bash
   .\venv\Scripts\Activate.ps1
   python scripts/etl/etl_sync_threading.py
   ```

3. **Luego iniciar Frontend**
   ```bash
   cd frontend
   npm run dev
   ```

### Para desarrollo completo:

1. **Backend + Frontend** (Opción 2)
   - Tienes acceso a cálculos avanzados
   - Puedes usar el toggle Supabase/Flask
   - Envío de emails funcional

---

## 📝 Notas Importantes

### ✅ Lo que funciona SIN Flask:
- ✅ Dashboard principal
- ✅ Listado de Letras (desde Supabase)
- ✅ Listado de Cobranzas (desde Supabase)
- ✅ Listado de Tesorería (desde Supabase)
- ✅ Navegación entre páginas
- ✅ UI completa y responsive

### ⚠️ Lo que requiere Flask:
- ⚠️ Cálculos de días vencidos
- ⚠️ Clasificación de antigüedad
- ⚠️ Cálculo de mora e intereses
- ⚠️ Envío de emails
- ⚠️ Exportación a Excel

### 💡 Estrategia Híbrida:
El sistema está diseñado para funcionar en **modo híbrido**:
- **Visualización rápida**: Supabase
- **Análisis profundo**: Flask API

---

## 🎉 ¡Listo!

Ahora puedes:
1. Iniciar solo el frontend: `cd frontend && npm run dev`
2. Ver la UI moderna en http://localhost:3000
3. Navegar entre módulos
4. Cuando necesites Flask, solo inícialo en otra terminal

**El frontend ya no depende de Flask para funcionar básicamente.** 🚀
