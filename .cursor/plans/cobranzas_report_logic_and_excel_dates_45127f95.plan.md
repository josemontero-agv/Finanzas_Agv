---
name: Cobranzas report logic and Excel dates
overview: "Alinear el módulo de cobranzas (reporte Cuenta 12) con la lógica definida en el prompt y el contexto del chat: fechas como tipo fecha en Excel, filtro dinámico por códigos de cuenta, corte histórico sin filtrar por amount_residual, exclusión de conciliados por saldo histórico, y UX del campo Códigos de Cuenta."
todos: []
isProject: false
---

# Plan: Cambios en el reporte del módulo de cobranzas

## Contexto

El reporte de cobranzas (Cuenta 12) debe cumplir:

- **Fechas en Excel**: exportar como tipo fecha real con formato `DD/MM/YYYY`, no como texto.
- **Cuenta 12**: filtro dinámico por prefijos de cuenta (`account_id.code =like 'X%'`) usando `account_codes`; sin dominios rígidos que excluyan cuentas válidas.
- **Corte histórico**: cuando hay `cutoff_date`, no filtrar por `amount_residual != 0` para no perder documentos ya pagados pero pendientes al corte.
- **Conciliados**: con corte y `include_reconciled=False`, excluir por saldo histórico al corte (`amount_residual_historical <= 0`), no por fecha de conciliación.
- **UX**: campo "Códigos de Cuenta" vacío por defecto con placeholder "Ingresa su cuenta contable".

Estado actual relevante:

- [app/collections/services.py](app/collections/services.py): dominio base con filtros de cuenta fijos (`account_id ilike '12'/'13'`, exclusiones 104/123/133) y `amount_residual != 0` siempre aplicado; exclusión de conciliados por `reconcile_date <= cutoff_date`.
- [app/exports/excel_service.py](app/exports/excel_service.py): fechas exportadas como texto con `format_date_for_export()`; no existe `parse_excel_date()` ni `cell.number_format = 'DD/MM/YYYY'` para columnas de fecha.
- [frontend/app/collections/page.tsx](frontend/app/collections/page.tsx): `DEFAULT_FILTERS.account_codes = '122,1212,123,1312,132,13'` (no vacío).

---

## 1. Backend – Dominio y lógica Cuenta 12 ([app/collections/services.py](app/collections/services.py))

### 1.1 Añadir `_parse_account_codes(account_codes)`

- Método estático que reciba `account_codes` (string o None).
- Si viene valor no vacío: split por coma, strip, devolver lista de códigos.
- Si viene vacío o None: devolver lista por defecto `['122', '1212', '123', '1312', '132', '13']`.

### 1.2 Reemplazar dominio de cuentas en `_build_report_domain`

- Eliminar del dominio base los términos actuales que usan `account_id` con `ilike` / `not ilike` (líneas ~195–204).
- Mantener solo: `account_id.reconcile = True` y `parent_state in (...)`.
- Usar `_parse_account_codes(account_codes)` y construir filtro por prefijo:
  - Para cada código `code`: `('account_id.code', '=like', f'{code}%')`.
  - Unir con `|` entre sí (un término por código). Si solo hay un código, un solo término; si hay varios, `['|', term1, '|', term2, term3, ...]` y añadirlos al domain.

### 1.3 Corte histórico: no filtrar por `amount_residual != 0`

- Quitar `('amount_residual', '!=', 0)` del dominio base.
- Añadir `('amount_residual', '!=', 0)` solo dentro del `else` (cuando no hay `cutoff_date`), junto con `start_date`, `end_date` y `reconciled` según corresponda.
- Con `cutoff_date` solo añadir `('date', '<=', cutoff_date)` (y no añadir filtro por residual).

### 1.4 Conciliados al corte por saldo histórico

- Donde se arma cada fila del reporte y se calcula `amount_residual_historical` (p.ej. ~468–470 y lógica similar en el otro flujo de reporte):
  - Después de calcular `amount_residual_historical`, si hay `cutoff_date` y `not include_reconciled` y `amount_residual_historical <= 0`, hacer `continue` (excluir la fila).
- Dejar de usar como criterio único de exclusión “conciliado antes del corte” por `reconcile_date <= cutoff_date`; el criterio de exclusión debe ser “saldo histórico al corte <= 0” cuando no se incluyen conciliados.

Comprobar que esta lógica se aplica en todos los flujos que generan líneas del reporte (p.ej. el que usa `get_report_lines` y el que pueda usar read_group o otro método).

---

## 2. Backend – Exportación Excel ([app/exports/excel_service.py](app/exports/excel_service.py))

### 2.1 Función `parse_excel_date(value)`

- Implementar en el ámbito del método de export (o como helper del servicio):
  - Si `value` es `None` o vacío → `None`.
  - Si es `datetime` → `value.date()`.
  - Si es str: tomar parte fecha (antes de espacio o de `T`), parsear con `datetime.strptime(..., '%Y-%m-%d')` y devolver `.date()`; en caso de error, `None`.
- Objetivo: que openpyxl reciba un objeto `date` para que la celda sea tipo fecha en Excel.

### 2.2 Columnas de fecha en `export_collections_report`

- Definir el conjunto de keys de columnas de fecha (las que corresponden a Fecha Factura, Fecha Contabilización, Fecha Vencimiento), alineado con las tuplas en `columns`: p.ej. `move_id/invoice_date`, `invoice_date`, `account.move/invoice_date`, `date`, `account.move/invoice_date_due`, `invoice_date_due`, `date_maturity`.
- En el bucle de escritura por fila/columna:
  - Para cada celda que corresponda a una de esas keys: obtener valor, convertir Many2One a string si aplica, luego `parsed = parse_excel_date(value)`.
  - Si `parsed` no es None: asignar `cell.value = parsed` y `cell.number_format = 'DD/MM/YYYY'`, y alineación centrada.
  - Si `parsed` es None y hay valor: usar `format_date_for_export(value)` como fallback (texto) y asignar a la celda (sin formato de fecha).
- Asegurar que ninguna columna de fecha quede solo con formato texto cuando el valor sea una fecha parseable.

---

## 3. Frontend – UX Códigos de Cuenta ([frontend/app/collections/page.tsx](frontend/app/collections/page.tsx))

- En `DEFAULT_FILTERS`, cambiar `account_codes: '122,1212,123,1312,132,13'` a `account_codes: ''`.
- Verificar que el input de "Códigos de Cuenta" tenga placeholder `"Ingresa su cuenta contable"` (y que no muestre un valor por defecto distinto cuando el estado inicial es vacío).

---

## 4. Verificación y changelog

- Probar reporte con y sin fecha de corte; con `account_codes` vacío (por defecto) y con valores (p.ej. `122,1212`).
- Descargar Excel y comprobar que las columnas de fecha son tipo fecha, ordenables/filtrables y con formato `DD/MM/YYYY`.
- Actualizar [changelog.md](changelog.md) con una entrada bajo "Mejorado" que refleje: fechas Excel como tipo fecha en export cobranzas; filtro dinámico por códigos de cuenta (Cuenta 12); corte histórico sin filtrar por residual; conciliados al corte por saldo histórico; UX Códigos de Cuenta vacío y placeholder.

---

## Resumen de archivos a tocar


| Archivo                                                                | Cambios                                                                                                                                                                         |
| ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [app/collections/services.py](app/collections/services.py)             | `_parse_account_codes`; dominio dinámico por `account_id.code`; `amount_residual != 0` solo sin cutoff; exclusión conciliados por `amount_residual_historical <= 0` con cutoff. |
| [app/exports/excel_service.py](app/exports/excel_service.py)           | `parse_excel_date()`; uso en columnas de fecha y `cell.number_format = 'DD/MM/YYYY'`.                                                                                           |
| [frontend/app/collections/page.tsx](frontend/app/collections/page.tsx) | `account_codes: ''` en defaults; placeholder del input.                                                                                                                         |
| [changelog.md](changelog.md)                                           | Entrada de mejoras del reporte cobranzas.                                                                                                                                       |


