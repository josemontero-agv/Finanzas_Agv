# Guía Odoo + Finanzas AGV (enfoque Cuenta 42): estructura, lógica y cómo unir Letras con Facturas

## 1) ¿Qué es este proyecto y qué busca?

**Finanzas AGV** es una webapp de reporting que consume datos desde **Odoo** (ERP) para construir reportes financieros operativos (Tesorería/Cobranzas/Letras) con:

- filtros más ágiles que Odoo
- “corte histórico” (estado al cierre de una fecha)
- KPI y resúmenes
- exportación a Excel
- UX (scroll infinito, loader global, modo oscuro)

**Objetivo principal (Cuenta 42)**: entregar una vista confiable de **Cuentas por Pagar (CxP)** que cuadre con los reportes contables de Odoo (Mayor / Aged Payable / análisis por cuenta) y permita rastrear documentos especiales como **Letras**.

---

## 2) Arquitectura de la webapp (cómo está organizada)

### 2.1 Capas

**A. Integración Odoo (XML‑RPC)**
- `app/core/odoo.py` → `OdooRepository`
  - `search_read`, `read`, `search_count`, `read_group`
  - Aquí se decide: qué modelo se consulta, qué filtros (domain) se usan y qué campos se leen.

**B. Servicios de dominio**
- `app/treasury/services.py` → `TreasuryService` (Cuenta 42 / CxP)
- `app/collections/services.py` → `CollectionsService` (Cuenta 12 / CxC)
- `app/letters/...` → funciones y vistas relacionadas a letras (cuando aplica)

**C. Rutas / Endpoints (Flask)**
- `app/treasury/routes.py` → `/api/v1/treasury/report/account42`
- `app/collections/routes.py` → cuenta 12
- `app/exports/routes.py` → exportación Excel

**D. UI (Jinja + Alpine + Axios)**
- `app/templates/treasury/report_account42.html` (UI CxP)
- `app/templates/collections/report_account12.html` (UI CxC)

---

## 3) Cómo funciona el reporte Cuenta 42 (lógica de negocio)

### 3.1 Qué consulta realmente

El reporte CxP se basa en:
- **`account.move.line`** (líneas contables)

Porque ahí están los campos contables “duros”:
- `debit`, `credit`
- `account_id` (cuenta contable 42/43/423xxxx)
- `date` (fecha contable)
- `amount_residual` (residual hoy)
- `matched_*` (conciliaciones)

Luego enriquece trayendo el encabezado:
- **`account.move`** (documento contable: factura, asiento, nota, etc.)

Ahí suelen estar:
- proveedor (`partner_id`), `ref`, `invoice_date`, `invoice_date_due`
- `payment_state` (estado funcional)
- `l10n_latam_document_type_id` (tipo doc LATAM)
- campos de letra (dependen de módulo/versión/custom)

### 3.2 Qué significa “Saldo” y por qué debe cuadrar con Odoo

En Odoo, el balance contable estándar es:

\[
\textbf{Saldo} = \textbf{Debe} - \textbf{Haber}
\]

Para cuentas de pasivo (42), lo normal es que el saldo sea **negativo** (acreedor).

> Si alguien calcula “Haber - Debe”, verá el signo invertido y no cuadrará visualmente con reportes estándar de Odoo.

### 3.3 Modo “corte histórico” (al 31/01, por ejemplo)

El “corte” intenta responder:
> “¿Cómo estaba la deuda al cierre del día X, aunque hoy ya esté pagada?”

La lógica típica es:
1) Traer líneas con `date <= cutoff_date` (lo existente contablemente hasta ese día).
2) No excluir conciliados (porque pueden estar conciliados hoy pero abiertos en el corte).
3) Usar conciliaciones parciales (`account.partial.reconcile`) para estimar pagos después del corte.
4) Reconstruir:
   - `pendiente_al_corte ≈ residual_actual + pagado_después_del_corte`

**Clave de cuadre**: depende de qué fecha usa Odoo para considerar “pago” (fecha del asiento de pago, fecha de conciliación, fecha del banco, etc.). Ese criterio debe alinearse con el reporte oficial que ustedes usan como “verdad”.

---

## 4) Odoo: entidades mínimas que debes entender (en lenguaje práctico)

### 4.1 `account.move` (Documento contable)
Piensa en esto como la cabecera del documento:
- factura proveedor, nota, asiento manual, pago, etc.

Campos clave:
- `name`, `ref`
- `move_type`
- `invoice_date`, `invoice_date_due`
- `partner_id`
- `payment_state`

### 4.2 `account.move.line` (Líneas contables)
Piensa en esto como “asientos por cuenta”:
- aquí están los cargos/abonos que afectan a 42/423xxxx.

Campos clave:
- `account_id.code`
- `debit`, `credit`
- `amount_residual`
- `reconciled`
- `matched_debit_ids`, `matched_credit_ids`

### 4.3 `account.partial.reconcile` (Conciliaciones)
Es el pegamento entre deuda y pagos:
- montos conciliados (parciales)
- fechas asociadas (según configuración/campo disponible)

### 4.4 `res.partner` (Proveedor)
Datos maestros: nombre, RUC, email, país.

### 4.5 `account.account` (Plan contable)
Define códigos como `4230002` y su jerarquía.

---

## 4.6 Terminología oficial de Odoo (ORM) — “modelo”, “registro”, “vista”, “acción”

Para hablar con un desarrollador Odoo en “modo oficial”, estas son las definiciones correctas:

- **Modelo (model)**: una **clase Python** que hereda de `models.Model` y se identifica por **`_name`** (ej. `account.move`).  
  - En Odoo, un modelo representa una “entidad de negocio” y su lógica (métodos, reglas, cálculos).

- **Tabla SQL (table)**: el lugar físico en PostgreSQL donde se almacenan los registros del modelo.  
  - Por defecto, Odoo crea/usa una tabla cuyo nombre suele coincidir con el modelo reemplazando `.` por `_` (ej. `account.move` → `account_move`), y se puede controlar con **`_table`** (cuando aplica).
  - **Importante**: en Odoo, “modelo ≈ tabla”, pero con matices por **herencia** y **campos calculados**.

- **Registro (record)**: una fila del modelo (ej. una factura específica dentro de `account.move`).  
  - En el ORM se maneja como *recordset*.

- **Herencia (inheritance)**:
  - **`_inherit`** puede usarse para extender un modelo existente (agregar campos/métodos).
  - También existe herencia “delegada” (delegation) y otros patrones; pero para tu caso lo clave es: *un mismo modelo puede representar múltiples tipos de documento mediante campos discriminantes* (ej. `move_type`).

- **Vista (view)**: definición UI almacenada en `ir.ui.view` (tree/list, form, kanban, pivot, graph…).  
  - La vista define **cómo se ve**, no qué registros se incluyen.

- **Acción de ventana (window action)**: definición en `ir.actions.act_window`.  
  - Una acción abre un modelo en una vista con un **domain** y un **context** específicos.

- **Menú (menuitem)**: `ir.ui.menu`.  
  - Un menú normalmente apunta a una acción.

- **Domain (dominio/filtro)**: lista de condiciones que Odoo aplica para seleccionar registros (ej. `[('move_type','=','in_invoice')]`).  
  - Esto explica por qué un registro “existe” pero “no aparece” en una pantalla: la acción/menú lo filtra.

- **Context (contexto)**: diccionario de flags/valores que cambian comportamiento en UI y en lógica (ej. defaults, company, idioma, etc.).

---

## 5) ¿Por qué hoy “no se puede unir” Letras con Facturas de manera confiable?

En Odoo, “letra” puede estar modelada de distintas formas:

### Caso A (ideal)
La letra es un `account.move` (o muy cercano) y existe relación explícita con la factura original.

### Caso B (común en custom)
La letra vive en un modelo custom y se generan asientos de canje/reclasificación.

### Caso C (frágil)
No hay relación formal; solo se “une” por texto (`ref`, `invoice_origin`, narraciones).

**Problema**: si no existe relación estructurada, unir por texto:
- se rompe con formatos distintos
- no escala
- no sirve para auditoría/cuadre

---

## 5.0 (Aclaración oficial Odoo) “¿Por qué la Letra vuelve a `account.move`?”

En Odoo, **`account.move` es el modelo estándar para cualquier documento contable** que genera asientos (líneas en `account.move.line`).  
Por eso, aunque el flujo de negocio sea “Factura → Planilla → Letra”, la **letra vuelve a `account.move`** porque:

- necesita generar contabilidad (débitos/créditos) y afectar cuentas (42/423xxxx)
- requiere fecha contable, vencimiento, partner, moneda, estado, etc.
- Odoo centraliza estos documentos contables en `account.move` y los distingue por campos como:
  - `move_type` (y/o diario `journal_id`, y/o campos custom)

**¿Por qué no se ve en la misma pantalla de facturas?**  
Porque el menú “Facturas de proveedor” abre una **acción** que filtra por `move_type` (y a veces por diarios). Si la letra se crea como `entry` (asiento) u otro tipo, **queda fuera del domain** de esa acción.

---

## 5.1 Lo que YA se ve en este repositorio: Planilla (`account.bill.form`) como puente Factura ↔ Letra

En tu repo existen scripts ETL/Investigación que muestran un flujo real:

### A) Modelo “planilla” de letras
- **Modelo**: `account.bill.form`
- Campos observados en scripts:
  - `invoice_ids` → facturas origen (IDs de `account.move`)
  - `move_ids` → letras generadas (IDs de `account.move`)
  - `partner_id`, `amount_total`, `state`, `name`

Esto sugiere el flujo:
**Factura(s) (`account.move`) → Planilla (`account.bill.form`) → Letras (`account.move`)**

### B) Relación directa desde la letra hacia la planilla / facturas
En los scripts del repo aparecen 2 variantes en `account.move` (letra):
- `bill_form_id` (Many2one hacia `account.bill.form`)
- `bill_form_invoices` (lista de IDs de facturas `account.move`)

Esto es crítico porque permite unir letra ↔ factura de forma estructurada (no texto).

### C) Campo “Número de letra”
En scripts del repo se usa `l10n_latam_boe_number`.  
Tú también mencionaste `l10n_latam_document_boe_number`.

Conclusión: el dev Odoo debe confirmar **cuál es el campo real** en TU base (y si existen ambos).

---

## 5.2 Trazabilidad práctica (para hablar con un dev Odoo con evidencia)

En tu repo ya existen scripts útiles:

### Script: inspeccionar `account.bill.form`
- `scripts/investigation/investigate_bill_form.py`
Qué hace:
- `fields_get` → lista campos del modelo
- lee registros recientes y muestra campos clave (`invoice_ids`, `move_ids`, etc.)

### Script: trazar flujo completo (pedido → factura → planilla → letra)
- `scripts/investigation/trace_document_flow.py`
Qué hace:
- toma una planilla reciente
- imprime facturas origen (`invoice_ids`)
- imprime letras generadas (`move_ids`) + BOE
- y si existe `invoice_origin`, intenta llegar a `sale.order`

Esto te permite explicarle al dev Odoo:
> “Hay un puente: `account.bill.form`. Para unir, hay que estandarizar campos y exponer relaciones en el reporte contable.”

---

## 6) Qué pedirle a un desarrollador Odoo (para lograr la unión)

### 6.1 Definir el objetivo funcional
Ejemplos:
- “En el reporte CxP quiero ver la factura y su(s) letra(s) asociada(s).”
- “Quiero agrupar por factura y listar letras.”
- “Quiero rastrear desde la letra hacia la factura origen y hacia el pago.”

### 6.2 Exigir relación de datos (no texto)
Se requiere una relación persistente:
- Opción recomendada: `account.move` (letra) tiene relación formal hacia factura(s).

Si ya existe `account.bill.form`, lo más sólido es:
- planilla referencia facturas (`invoice_ids`)
- planilla referencia letras (`move_ids`)
- letra referencia planilla (`bill_form_id`)

### 6.3 Definir el “campo número de letra”
El dev Odoo debe confirmar:
- en qué modelo vive
- nombre técnico exacto
- si es calculado o almacenado
- si cambia por versión/localización

### 6.4 Alinear corte histórico (criterio contable)
Pedir:
- cuál es el reporte oficial de corte que usan (Mayor vs Aged Payable vs análisis)
- qué fecha considera para pagos en corte
- qué dominios usa (move_types, posted, company_id, etc.)

### 6.5 Checklist concreto para reunión con el dev Odoo
1) ¿La letra es un `account.move`? ¿Qué `move_type` usa?
2) Confirmar `account.bill.form`:
   - campos `invoice_ids` y `move_ids`
3) En `account.move` (letra), confirmar:
   - `bill_form_id` y/o `bill_form_invoices`
4) Confirmar campo de “Número Letra”:
   - `l10n_latam_boe_number` vs `l10n_latam_document_boe_number` vs custom
5) ¿Dónde está el estado de la letra (`portfolio`, `to_accept`, etc.) y qué significa operativamente?
6) Confirmar qué fecha usa Odoo para “pagado” al corte.

---

## 7) ¿Recomiendo estudiar Odoo como desarrollador?

**Sí, pero de forma enfocada.**  
No necesitas convertirte en “core developer” de Odoo para entregar valor. Lo rentable es dominar:
- contabilidad: `account.move`, `account.move.line`
- conciliación: `account.partial.reconcile`
- dominios y relaciones (Many2one/One2many/Many2many)
- y el flujo real de letras en tu instancia (planilla ↔ facturas ↔ letras ↔ pagos)

### Ruta recomendada (práctica)
**Nivel 1 (1–2 semanas):**
- `account.move` / `account.move.line`
- `payment_state` vs `reconciled`
- `invoice_date` vs `date`
- qué es `amount_residual` y cómo cambia

**Nivel 2 (1–2 semanas):**
- conciliaciones parciales (`account.partial.reconcile`)
- multi‑moneda (moneda origen vs moneda compañía)
- cómo Odoo calcula saldo (Debe - Haber)

**Nivel 3 (según implementación):**
- modelo real de letras (planilla, campos custom, estados)
- relación formal factura ↔ letra
- reporte unificado con trazabilidad (factura → letra → pago)

---

## 8) A dónde se quiere llegar (visión técnica)

Estado final “maduro”:
- Reporte CxP unificado que muestre por fila:
  - factura (proveedor, fechas, ref, tipo doc)
  - cuenta contable (423xxxx)
  - letra (número, vencimiento, estado)
  - pagos/conciliaciones (fecha, monto)
  - corte histórico confiable (cuadra con Odoo)

Para llegar ahí, requisito n°1:
> Odoo debe proveer una relación estructurada factura ↔ letra (no por texto).


