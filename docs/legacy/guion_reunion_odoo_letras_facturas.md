# Guion de reunión (Odoo) — Unión Facturas ↔ Letras (Cuenta 42) + Corte Histórico

## 1) Objetivo de la reunión (1 minuto)

**Meta:** definir de forma **estructurada** (campos/relaciones) cómo se conectan:

- Factura(s) de proveedor (CxP)
- Planilla (si aplica)
- Letras generadas
- Pagos/conciliaciones

…para que el reporte web de **Cuenta 42** pueda mostrar trazabilidad y cuadre al **corte histórico**.

**Regla de oro:** nada de “unir por texto”; debe existir relación formal (Many2one/One2many/M2M) o al menos un puente único (ej. `account.bill.form`).

---

## 2) Alcance funcional acordado (5 minutos)

Pedir que definan cuál de estos escenarios quieren (elige 1 o más):

- **A) Vista por Factura:** cada factura muestra sus letras asociadas y su estado.
- **B) Vista por Letra:** cada letra muestra las facturas que incluye/origina y su estado.
- **C) Vista contable (Cuenta 42):** cada línea contable (423xxxx) debe indicar si corresponde a una letra y a qué factura(s) está relacionada.

**Salida esperada (para el usuario):**
- En el reporte de Cuenta 42: columna “Número Letra”, “Planilla”, “Factura Origen”, “Estado Letra”, “Fecha Letra”, “Vencimiento Letra”.

---

## 3) Diagrama mínimo (lo que queremos modelar)

### Opción recomendada (por lo visto en tu repo)

- `account.bill.form` (Planilla)
  - `invoice_ids` → facturas origen (`account.move`)
  - `move_ids` → letras generadas (`account.move`)

- `account.move` (Letra)
  - `bill_form_id` → planilla (`account.bill.form`)
  - opcional: `bill_form_invoices` → facturas (`account.move`) si existe

**Trazabilidad:**

Factura(s) (`account.move`, in_invoice)  
→ Planilla (`account.bill.form`)  
→ Letra(s) (`account.move`, tipo letra)  
→ Pagos/conciliaciones (`account.partial.reconcile`)

---

## 4) Preguntas clave (checklist) — para el dev Odoo

### 4.1 Modelado de Letras
- **¿Qué modelo representa la Letra?**
  - ¿Es `account.move` o un modelo custom?
- **¿Qué `move_type` usa la letra?**
  - Ej: `entry`, `in_invoice`, `in_receipt`, u otro custom/flujo.
- **¿Qué campo almacena el estado de la letra?**
  - Ej: estados tipo `portfolio`, `to_accept`, etc. ¿En qué campo viven y qué significan?

### 4.2 Relación Factura ↔ Letra
- ¿Existe el modelo `account.bill.form` en tu base?
  - Confirmar campos: `invoice_ids`, `move_ids`, `partner_id`, `state`, `amount_total`.
- En `account.move` (letras), ¿existe `bill_form_id`?
- En `account.move` (letras), ¿existe `bill_form_invoices` (lista de facturas)?
- Si NO existe relación formal:
  - ¿Cuál es la fuente de verdad para vincular letra a factura? (y proponer campo/relación)

### 4.3 Campo “Número Letra” (BOE)
- ¿Cuál es el nombre técnico del campo?
  - `l10n_latam_boe_number` vs `l10n_latam_document_boe_number` vs custom
- ¿En qué modelo vive? (`account.move` letra, factura, o planilla)
- ¿Está almacenado (store=True) o calculado (compute)?  
  - Si es compute, ¿tiene problemas de performance / acceso vía XML‑RPC?

### 4.4 Contabilidad (Cuenta 42) y origen del saldo
- ¿Qué cuentas exactas se consideran letras? (ej. `4230002`, `4230003`)
- ¿La letra impacta contablemente la 42 directamente en las líneas (`account.move.line`)?
  - Si no, ¿qué asiento/flujo la mueve a 42?

### 4.5 Corte histórico (al 31/01)
- ¿Qué reporte oficial usan como “verdad” para el corte? (Mayor / Aged Payable / análisis)
- ¿Qué fecha usan para considerar “pagado” al corte?
  - fecha del pago, fecha del asiento, fecha conciliación, fecha banco
- ¿Qué dominio exacto usan? (posted, compañías, diarios, move_types)
- ¿Cómo tratan multi-moneda en letras? (USD vs PEN; tipo de cambio al cierre)

---

## 5) Entregables que debe dejar la reunión

### 5.1 Documento técnico (1 página)
- Lista de modelos involucrados
- Campos y relaciones oficiales (con nombre técnico)
- Dominio/reporte oficial para “corte”

### 5.2 Ejemplos reales (mínimo 3 casos)
Para cada caso, entregar IDs y valores:
- 1 factura con 1 letra
- 1 factura con varias letras (si aplica)
- 1 letra que agrupa varias facturas (si aplica)

Con eso, el equipo web valida trazabilidad y cuadre.

---

## 6) Requerimiento mínimo (para que tu web sí pueda “unir”)

Tu web solo necesita una de estas 2 soluciones (preferible la A):

### A) Relación estructurada vía planilla
- `account.bill.form.invoice_ids` (facturas)
- `account.bill.form.move_ids` (letras)
- `account.move.bill_form_id` (letra → planilla)

### B) Relación directa letra ↔ factura
- `account.move` (letra) tiene `invoice_ids` (M2M) o `invoice_id` (M2O) hacia factura(s)

Sin una relación así, cualquier “unión” será frágil (texto) y no auditable.

---

## 7) Próximo paso sugerido (muy práctico)

Ejecutar (con el dev Odoo) los scripts existentes del repo:
- `scripts/investigation/investigate_bill_form.py`
- `scripts/investigation/trace_document_flow.py`

Y confirmar:
- los campos reales en tu Odoo
- el flujo real de planilla/facturas/letras
- el campo correcto de “Número Letra”


