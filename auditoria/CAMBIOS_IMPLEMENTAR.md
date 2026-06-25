# Cambios a Implementar — Finanzas AGV
> Generado el 23/06/2026 — Resumen de cambios del chat anterior para implementación en nuevo agente.

---

## CONTEXTO DEL PROYECTO

- **Backend:** Flask + Python (`app/collections/services.py`, `app/collections/routes.py`, `app/exports/excel_service.py`)
- **Frontend:** Next.js + TypeScript (`frontend/app/collections/page.tsx`, `frontend/lib/api.ts`)
- **ORM:** Odoo XML-RPC (`account.move.line` → `account.move` → `sale.order`)
- **Reporte principal:** Cuentas por Cobrar Cuenta 12

---

## CAMBIO 1 — Sub Canal desde Orden de Venta

**Archivo:** `app/collections/services.py`

**Problema actual:** El campo `sub_channel` se extrae de `agr.credit.customer/sub_channel_id`.  
**Cambio requerido:** Extraerlo desde `move_id/order_id/sub_channel_id` (orden de venta vinculada al asiento).

### Paso 1: Agregar `order_id` a `move_fields` (hacer en AMBAS funciones: `get_report_lines` y `get_report_lines_paginated`)

Buscar el bloque:
```python
move_fields = [
    'id', 'name', 'state', 'move_type', 'bill_form_id',
    ...
    'bill_form_invoices_order_sales_line_commercial_zone_id',
]
```
Agregar al final de la lista: `'order_id'`

### Paso 2: Construir `order_map` después de `trace_invoice_map` (en AMBAS funciones)

Insertar después de `trace_invoice_map = self._build_trace_invoice_map(move_map)`:

```python
# Construir mapa de órdenes de venta para obtener sub_channel_id (move_id/order_id/sub_channel_id)
order_map = {}
order_ids_set = set()
for m in move_map.values():
    oid = m.get('order_id')
    if isinstance(oid, list) and oid and oid[0]:
        order_ids_set.add(oid[0])
if order_ids_set:
    try:
        orders = self._read_in_batches('sale.order', list(order_ids_set), ['id', 'sub_channel_id', 'tag_ids'], batch_size=300)
        order_map = {o['id']: o for o in orders}
    except Exception as e:
        print(f"[WARN] No se pudo obtener sale.order para sub_channel_id: {e}")

# Mapa de etiquetas (tag_ids → nombre) para método de pago
tag_map = {}
try:
    all_tag_ids = set()
    for o in order_map.values():
        for tid in (o.get('tag_ids') or []):
            all_tag_ids.add(tid)
    if all_tag_ids:
        tags = self.repository.read('crm.tag', list(all_tag_ids), ['id', 'name'])
        tag_map = {t['id']: t.get('name', '') for t in tags}
except Exception as e:
    print(f"[WARN] No se pudo obtener nombres de etiquetas (crm.tag): {e}")
```

### Paso 3: Reemplazar lógica de sub_channel_raw (en AMBAS funciones)

**Buscar y reemplazar:**
```python
# ANTES:
sub_channel_raw = m2o_name(credit.get('sub_channel_id'))
```
**Por:**
```python
# DESPUÉS:
# Determinar Sub Canal desde move_id/order_id/sub_channel_id
order_id_val = move.get('order_id') or source_move.get('order_id')
if isinstance(order_id_val, list) and order_id_val and order_id_val[0]:
    order = order_map.get(order_id_val[0], {})
    sub_channel_raw = m2o_name(order.get('sub_channel_id'))
else:
    sub_channel_raw = ''
```

---

## CAMBIO 2 — Optimización Foto Histórica (Fecha de Corte)

**Archivo:** `app/collections/services.py`

### Paso 1: Modificar `_build_report_domain`

**Firma actual:**
```python
def _build_report_domain(self, start_date=None, end_date=None, customer=None,
                        account_codes=None, sales_channel_id=None, doc_type_id=None,
                        sub_channel=None,
                        cutoff_date=None, include_reconciled=False):
```
**Firma nueva:**
```python
def _build_report_domain(self, start_date=None, end_date=None, customer=None,
                        account_codes=None, sales_channel_id=None, doc_type_id=None,
                        sub_channel=None, date_cutoff_start=None,
                        cutoff_date=None, include_reconciled=False):
```

**Buscar en el cuerpo:**
```python
if cutoff_date:
    domain.append(('date', '<=', cutoff_date))
```
**Reemplazar por:**
```python
if cutoff_date:
    # Cota inferior dinámica — evita traer partidas de años anteriores ya cerrados
    FISCAL_YEAR_START = date_cutoff_start or '2026-01-01'
    domain.append(('date', '>=', FISCAL_YEAR_START))
    domain.append(('date', '<=', cutoff_date))
```

### Paso 2: Agregar `estado_historico` al loop de procesamiento (en AMBAS funciones)

**Buscar:**
```python
current_residual = abs(line.get('amount_residual', 0.0) or 0.0)
amount_residual_historical = current_residual
if cutoff_date:
    amount_residual_historical = current_residual + paid_after_cutoff
    if reconcile_date and reconcile_date <= cutoff_date and include_reconciled:
        amount_residual_historical = 0.0
    if not include_reconciled and amount_residual_historical <= 0:
        continue
```
**Reemplazar por:**
```python
current_residual = abs(line.get('amount_residual', 0.0) or 0.0)
amount_residual_historical = current_residual
estado_historico = ''
if cutoff_date:
    amount_residual_historical = current_residual + paid_after_cutoff
    if reconcile_date and reconcile_date <= cutoff_date and include_reconciled:
        amount_residual_historical = 0.0

    # Estado al corte: PAGADA si saldo histórico <= 0, NO PAGADA si hay deuda pendiente
    estado_historico = 'PAGADA' if amount_residual_historical <= 0 else 'NO PAGADA'

    if not include_reconciled and amount_residual_historical <= 0:
        continue
```

### Paso 3: Agregar `estado_historico` al diccionario `row` (en AMBAS funciones)

En el dict `row`, junto a los campos calculados, agregar:
```python
'estado_historico': estado_historico,
```

---

## CAMBIO 3 — Filtro Método de Pago (`move_id/order_id/tag_ids`)

**Archivo:** `app/collections/services.py`

### Paso 1: Agregar parámetros a `get_report_lines`

**Firma actual:**
```python
def get_report_lines(self, start_date=None, end_date=None, customer=None, limit=0,
                     account_codes=None, sales_channel_id=None, doc_type_id=None,
                     sub_channel=None,
                     cutoff_date=None, include_reconciled=False):
```
**Firma nueva:**
```python
def get_report_lines(self, start_date=None, end_date=None, customer=None, limit=0,
                     account_codes=None, sales_channel_id=None, doc_type_id=None,
                     sub_channel=None, date_cutoff_start=None, payment_method=None,
                     cutoff_date=None, include_reconciled=False):
```

### Paso 2: Pasar `date_cutoff_start` en el llamado a `_build_report_domain`

Agregar `date_cutoff_start=date_cutoff_start,` al llamado dentro de `get_report_lines`.

### Paso 3: Agregar filtro de pago en el loop de líneas (en AMBAS funciones)

Después del filtro de `sub_channel`, insertar:
```python
# Determinar Método de Pago desde sale.order.tag_ids
order_for_tags = order_map.get(order_id_val[0], {}) if isinstance(order_id_val, list) and order_id_val else {}
order_tag_ids = order_for_tags.get('tag_ids') or []
payment_method_display = ', '.join(
    tag_map[tid] for tid in order_tag_ids if tid in tag_map
)

# Filtro post-proceso por método de pago (ID de crm.tag)
if payment_method and str(payment_method).strip():
    try:
        pm_id = int(payment_method)
        if pm_id not in order_tag_ids:
            continue
    except (ValueError, TypeError):
        pass
```

### Paso 4: Agregar campos al dict `row`

```python
'payment_method': payment_method_display,
'move_id/order_id/tag_ids': payment_method_display,
```

### Paso 5: En `get_report_lines_paginated`, agregar extracción de kwargs

```python
date_cutoff_start = kwargs.get('date_cutoff_start')
payment_method = kwargs.get('payment_method')
```

### Paso 6: Agregar `payment_methods` a `get_filter_options`

Agregar al cuerpo de la función (antes del `return`):

```python
# Obtener métodos de pago siguiendo la ruta move_id/order_id/tag_ids
payment_methods = []
try:
    order_tag_rows = self.repository.search_read(
        'sale.order',
        [('tag_ids', '!=', False)],
        ['tag_ids'],
        limit=5000
    )
    tag_ids_set = set()
    for row in order_tag_rows:
        for tid in (row.get('tag_ids') or []):
            tag_ids_set.add(tid)
    if tag_ids_set:
        tag_records = self.repository.read('crm.tag', list(tag_ids_set), ['id', 'name'])
        payment_methods = [
            {'id': t['id'], 'name': t.get('name', '')}
            for t in tag_records if t.get('name')
        ]
        payment_methods.sort(key=lambda x: x['name'])
except Exception as e:
    print(f"[WARN] No se pudo obtener métodos de pago (move_id/order_id/tag_ids): {e}")
```

Agregar `'payment_methods': payment_methods` en todos los `return` de `get_filter_options` (incluidos los de error/fallback).

---

## CAMBIO 4 — Routes

**Archivo:** `app/collections/routes.py`

En el endpoint `report_account12`, agregar extracción de parámetros:
```python
date_cutoff_start = request.args.get('date_cutoff_start')
payment_method = request.args.get('payment_method')
```

Pasarlos en TODAS las llamadas a `get_report_lines` y `_build_report_domain`:
```python
date_cutoff_start=date_cutoff_start,
payment_method=payment_method,
```

Incluirlos en `filters_applied`:
```python
'date_cutoff_start': date_cutoff_start,
'payment_method': payment_method,
```

---

## CAMBIO 5 — Frontend: Tipos TypeScript

**Archivo:** `frontend/lib/api.ts`

### Agregar a `ReportParams`:
```typescript
export interface ReportParams {
  // ...campos existentes...
  date_cutoff_start?: string   // NUEVO
  payment_method?: string      // NUEVO
}
```

### Agregar a `FilterOptions`:
```typescript
export interface FilterOptions {
  sales_channels: Array<{ id: number; name: string }>
  document_types: Array<{ id: number; name: string }>
  sub_channels: Array<{ value: string; name: string }>
  payment_methods: Array<{ id: number; name: string }>  // NUEVO
}
```

---

## CAMBIO 6 — Frontend: UI de Filtros

**Archivo:** `frontend/app/collections/page.tsx`

### Paso 1: Actualizar `DEFAULT_FILTERS`
```typescript
const DEFAULT_FILTERS: ReportParams = {
  date_from: '',
  date_to: '',
  date_cutoff: '',
  date_cutoff_start: '',   // NUEVO
  customer: '',
  sub_channel: '',
  payment_method: '',      // NUEVO
  account_codes: '',
  sales_channel_id: undefined,
  doc_type_id: undefined,
  include_reconciled: false,
}
```

### Paso 2: Ocultar filtros "Fecha Desde" y "Fecha Hasta"

Eliminar completamente los dos `<div>` con labels "Fecha Desde" y "Fecha Hasta" del JSX.

### Paso 3: Agregar "Fecha Inicio (Origen)" en filtros principales

Insertar ANTES del `<div>` de "Fecha de Corte":
```tsx
<div className="space-y-2">
  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Fecha Inicio (Origen)</label>
  <Input
    type="date"
    value={draftFilters.date_cutoff_start}
    onChange={(e) => handleFilterChange('date_cutoff_start', e.target.value)}
    className="focus-visible:ring-[#714B67] dark:focus-visible:ring-purple-500 border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
  />
</div>
```

### Paso 4: Agregar "Método de Pago" en filtros avanzados

Insertar ANTES del `<div>` de "Sub Canal":
```tsx
<div className="space-y-2">
  <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">Método de Pago</label>
  <select
    className="w-full h-10 px-3 py-2 text-sm bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-slate-700 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-[#714B67] dark:focus:ring-purple-500 focus:ring-offset-0 disabled:opacity-50"
    value={draftFilters.payment_method || ""}
    onChange={(e) => handleFilterChange('payment_method', e.target.value)}
  >
    <option value="">Todos los métodos</option>
    {filterOptions?.payment_methods?.map(pm => (
      <option key={pm.id} value={pm.id.toString()}>{pm.name}</option>
    ))}
  </select>
</div>
```

### Paso 5: Agregar columna "Método de Pago" en la tabla

En el array `columns`, insertar ANTES de la entrada de `sub_canal`:
```typescript
{ key: "metodo_pago", label: "Método de Pago", get: (row: any) => firstValue(row, ["payment_method", "move_id/order_id/tag_ids"]), maxWidth: "max-w-[200px]" },
```

---

## CAMBIO 7 — Excel Service: Limpieza y Nuevas Columnas

**Archivo:** `app/exports/excel_service.py`

### Eliminar de `export_collections_report` y `export_treasury_report`:

1. Quitar de la lista `columns`:
   - `(('amount_residual_historical',), 'Monto Residual al Corte')`
   - `(('paid_after_cutoff',), 'Pagos Posteriores al Corte')`

2. En `export_collections_report`, quitar `amount_residual_historical` del fallback de "Monto Residual":
   ```python
   # ANTES:
   (('account.move/amount_residual', 'amount_residual_with_retention', 'amount_residual_historical'), 'Monto Residual'),
   # DESPUÉS:
   (('account.move/amount_residual', 'amount_residual_with_retention'), 'Monto Residual'),
   ```

3. En todos los sets de `numeric_keys` y de formato `#,##0.00`, quitar `'amount_residual_historical'` y `'paid_after_cutoff'`.

### Agregar a `export_collections_report`:

En la lista `columns`, agregar estas dos entradas (ANTES de la columna de Sub Canal):
```python
(('payment_method', 'move_id/order_id/tag_ids'), 'Método de Pago'),
(('agr.credit.customer/sub_channel_id', 'sub_channel_id'), 'Sub Canal'),  # ya existente
```

Al final de la lista, agregar:
```python
(('estado_historico',), 'Estado al Corte'),
```

Agregar formato condicional para `estado_historico` en el bloque de estilos de celda:
```python
elif 'estado_historico' in key_candidates:
    cell.alignment = Alignment(horizontal='center')
    if value == 'PAGADA':
        cell.fill = PatternFill(start_color="CCFFCC", end_color="CCFFCC", fill_type="solid")
        cell.font = Font(color="006100", bold=True)
    elif value == 'NO PAGADA':
        cell.fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        cell.font = Font(color="9C0006", bold=True)
```

---

## NOTAS IMPORTANTES

- La variable `amount_residual_historical` y `paid_after_cutoff` **se mantienen en el dict `row`** (son necesarias para el cálculo de KPIs en `routes.py`). Solo se eliminan de las columnas visibles del Excel.
- El filtro `payment_method` aplica **post-proceso** (Python), no en el domain de Odoo, igual que `sub_channel`.
- El filtro `date_cutoff_start` aplica **en el domain de Odoo** (campo `date` indexado en `account.move.line`).
- El `tag_map` y el `order_map` con `tag_ids` se construyen en **ambas funciones** (`get_report_lines` y `get_report_lines_paginated`).
