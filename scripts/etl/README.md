# ETL Odoo → Supabase — Guía operativa

Scripts para sincronizar datos de Odoo hacia Supabase y validar paridad antes de activar `COLLECTIONS_SOURCE=supabase` en producción.

## Prerrequisitos

- Python 3.11+ con dependencias instaladas (`pip install -r requirements.txt`).
- Entorno virtual en la raíz del repo: `venv\`.
- Variables en `.env.produccion` (ETL y paridad contra Odoo/Supabase reales) o `.env.desarrollo` (pruebas locales).
- `SUPABASE_URL` + `SUPABASE_KEY` (service role) para el ETL.
- `SUPABASE_DB_URI` (pooler Postgres `:6543`) para el script de paridad y el backend con `COLLECTIONS_SOURCE=supabase`.

## Cuándo correr el ETL

| Situación | Acción |
|-----------|--------|
| **Primera carga** o datos desactualizados tras cambios en Odoo | Correr ETL completo (ver abajo). |
| **Re-sync histórico de líneas CxC** (paridad falla en totales) | 1) `reset_watermark.ps1` → 2) `run_etl.ps1` → 3) `run_parity.ps1`. |
| **Producción Render** | Cron cada 15 min (`render.yaml`); no hace falta correr manual salvo incidentes. |
| **Desarrollo UI sin Supabase** | No correr ETL; usar `COLLECTIONS_SOURCE=odoo` (default). |

El ETL incremental usa marcas de agua en `etl_sync_state`. Si existe `last_synced_at` para un modelo, solo trae registros con `write_date` posterior. Sin watermark → sync histórico completo paginado.

Modelos Cobranzas (Fase 3):

- `account.move.line.collections` → `fact_move_lines`
- `account.partial.reconcile` → `fact_partial_reconciles`
- Dimensiones: cuentas, canales, tipos doc, clientes crédito, órdenes de venta

## APP_ENV=production

El ETL y la paridad deben apuntar al mismo entorno que producción:

```powershell
$env:APP_ENV = "production"   # carga .env.produccion
```

`run_etl.ps1` y `run_parity.ps1` ya fijan esto. **No uses `.env.desarrollo` para validar go-live** salvo que Odoo y Supabase estén alineados explícitamente en ese archivo.

## Scripts PowerShell (Windows)

Ejecutar desde cualquier carpeta; los scripts resuelven la raíz del repo automáticamente.

### `run_etl.ps1`

Sincronización completa Odoo → Supabase (facturas, letras, dimensiones Cobranzas, líneas, conciliaciones).

```powershell
.\scripts\etl\run_etl.ps1
```

Equivalente manual:

```powershell
$env:APP_ENV = "production"
.\venv\Scripts\python.exe scripts\etl\etl_sync_threading.py
# o: python -m scripts.etl.etl_sync_threading
```

**Duración:** puede tardar varios minutos en re-sync histórico (~78k líneas CxC). Revisar logs en consola.

### `reset_watermark.ps1`

Borra la marca de agua de `account.move.line.collections` en `etl_sync_state` para forzar re-importación histórica de `fact_move_lines`.

```powershell
.\scripts\etl\reset_watermark.ps1
```

**Requiere acceso SQL a Supabase** (una de estas vías):

1. **Supabase Dashboard** → SQL Editor → pegar y ejecutar el SQL que imprime el script.
2. **Supabase MCP** (Cursor): `execute_sql` con el mismo `DELETE`.
3. **psql** con `SUPABASE_DB_URI` del `.env` activo:

```powershell
$env:APP_ENV = "production"
# cargar URI y ejecutar DELETE (ver salida del script)
```

Tras reset, correr `run_etl.ps1` y luego `run_parity.ps1`.

Para reset completo de todos los modelos Cobranzas (opcional, solo si hace falta):

```sql
DELETE FROM public.etl_sync_state
WHERE model_name IN (
  'account.move.line.collections',
  'account.partial.reconcile',
  'dim.accounts',
  'dim.sales_channels',
  'dim.doc_types',
  'dim.credit_customers',
  'dim.sale_orders'
);
```

### `run_parity.ps1`

Compara totales Odoo vs Supabase (`test_collections_parity.py` en la raíz del repo).

```powershell
.\scripts\etl\run_parity.ps1
.\scripts\etl\run_parity.ps1 -Env desarrollo
```

- Exit code **0** → todos los escenarios `MATCH`.
- Exit code **1** → hay `DIFF` (no activar `COLLECTIONS_SOURCE=supabase` en Render).

Criterio go-live: **3/3 escenarios MATCH** (sin filtros, rango de fechas, con fecha de corte).

### `check_odoo.ps1`

Confirma que las credenciales `ODOO_*` del `.env` activo autentican contra Odoo y que una consulta de solo lectura (`search_read`) funciona. Útil antes del ETL o si `/api/health` marca Odoo en `disconnected`/`error`.

```powershell
.\scripts\etl\check_odoo.ps1
.\scripts\etl\check_odoo.ps1 -Env produccion
.\scripts\etl\check_odoo.ps1 -Env desarrollo -Model account.move -Limit 3
```

Equivalente manual:

```powershell
$env:APP_ENV = "development"   # o production
.\venv\Scripts\python.exe scripts\etl\check_odoo.py --env desarrollo
```

Solo lectura; no escribe en Odoo. La contraseña/API Key se muestra enmascarada.

## Modos de trabajo local

| Modo | `COLLECTIONS_SOURCE` | Backend | Fuente Cobranzas | Cuándo usarlo |
|------|----------------------|---------|------------------|---------------|
| **A — UI / Odoo vivo** | `odoo` (default) | `python run.py` | Odoo XML-RPC | Desarrollo de pantallas, filtros rápidos |
| **B — Validar Supabase** | `supabase` | `python run.py production` + ETL previo | Supabase Postgres | Antes de go-live; debe pasar paridad |
| **C — Producción** | `supabase` | Render | Supabase + cron ETL | Operación normal |

Flujo recomendado **Modo B**:

1. `run_etl.ps1` (o re-sync tras `reset_watermark.ps1`).
2. En `.env.produccion` o sesión: `COLLECTIONS_SOURCE=supabase`.
3. `python run.py production` → probar `/collections` en el navegador.
4. `run_parity.ps1` → confirmar 3/3 MATCH.

Tesorería sigue leyendo **Odoo** en todos los modos (aún no migrada).

## Paridad — qué valida el script

`test_collections_parity.py` ejecuta tres escenarios:

1. Sin fecha, `limit=200`
2. Último mes (`start_date` / `end_date`)
3. Con `cutoff_date` (incluye métricas históricas: `pending_cutoff`, `amount_residual_historical`, `paid_after_cutoff`, `paid_before_cutoff`)

Compara conteo y sumas entre `CollectionsService` (Odoo) y `CollectionsSupabaseProvider` (Supabase). Solo lectura; no modifica datos.

## Esquema y referencias

- `supabase_schema_etl_state.sql` — tabla `etl_sync_state`
- `supabase_schema_collections.sql` — tablas del piloto Cobranzas
- `etl_sync_threading.py` — implementación del sync
- `check_odoo.py` — diagnóstico de credenciales y consulta de lectura a Odoo
- `app/collections/supabase_provider.py` — lectura en backend cuando `COLLECTIONS_SOURCE=supabase`

## Troubleshooting

| Síntoma | Posible causa |
|---------|----------------|
| Paridad DIFF en conteos | Watermark parcial; reset + re-ETL |
| Paridad DIFF en residual con cutoff | Revisar `fact_partial_reconciles`; cuenta 123 (letras) tiene limitaciones conocidas |
| ETL falla auth Odoo | Revisar `ODOO_*` en el `.env` del `APP_ENV` activo; correr `check_odoo.ps1` |
| `check_odoo` FALLO en authenticate | Usuario/API Key o `ODOO_DB` incorrectos; 2FA requiere API Key en `ODOO_PASSWORD` |
| `check_odoo` no contacta el servidor | `ODOO_URL` mal formado, red/VPN o timeout |
| Paridad no conecta Supabase | `SUPABASE_DB_URI` debe ser connection string pooler (`:6543`), no URL REST |
| Backend vacío con `supabase` | ETL no corrido o tablas vacías; verificar `/diagnostics` en frontend |
