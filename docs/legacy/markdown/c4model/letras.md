# 📄 Módulo de Letras - Investigación y Modelo

Documento técnico que resume el modelado de Letras en Odoo, la customización aplicada en Finanzas AGV y los artefactos de Structurizr añadidos para generar diagramas específicos del dominio de Letras.

---

## 🔍 Hallazgos de modelado en Odoo

- **Modelo principal:** `account.move` se usa como la entidad de letra. Campos clave: `state` (usa valor custom `to_accept`), `l10n_latam_boe_number` (número de letra), `acceptor_id`, `partner_id`, `bill_form_id`, `bill_form_invoices`, `invoice_user_id`, `currency_id`, `invoice_date`, `invoice_date_due`, `invoice_origin`, `ref`.
- **Relaciones directas:**
  - `partner_id` / `acceptor_id` → `res.partner` (RUC, ciudad, email).
  - `invoice_user_id` → `res.users` (vendedor).
  - `currency_id` → `res.currency` (código de moneda).
  - `bill_form_id` → `account.bill.form` / `agr.bill.form` / `bill.form` (planilla de letras) con `invoice_ids` que devuelven los números de factura originales.
- **Estado calculado en aplicación:** la UI calcula `status_calc` usando la fecha de emisión (`invoice_date`) y la ciudad del cliente: Lima > 4 días ⇒ `POR RECUPERAR`; Provincia > 10 días ⇒ `POR RECUPERAR`; caso contrario `VIGENTE`.
- **Trazabilidad**: las planillas (`account.bill.form`) enlazan facturas (`invoice_ids`) y letras (`move_ids`), permitiendo el flujo Pedido → Factura → Planilla → Letras.

Referencias de código:

```90:152:app/letters/letters_service.py
# Dominio to_accept y campos extraídos de account.move
```

```197:359:app/letters/letters_service.py
# Resolución de bill_form_id, carga de invoice_ids y cálculo de status_calc
```

```51:108:scripts/investigation/trace_document_flow.py
# Flujo: planilla (account.bill.form) -> facturas (invoice_ids) -> letras (move_ids)
```

---

## 🧭 Dominios y vistas en Odoo

- **Dominios usados por la API:**
  - `('state', '=', 'to_accept')` para letras pendientes de aceptación (se filtra con `l10n_latam_boe_number` si existe).
  - En pruebas directas: `('l10n_latam_boe_number', '!=', False)` y `('l10n_latam_boe_number', '!=', '')` para asegurar letras numeradas.
- **Vistas relacionadas:** el script de investigación busca `ir.ui.view` sobre `account.move` que contengan `letter` o `boe` en el nombre para identificar formularios/listas custom del módulo de letras. Ejecutar el script en un entorno conectado devuelve los tipos (`form`, `tree`, etc.) y nombres efectivos.
- **Menús y acciones:** se buscan entradas de menú con nombre que contenga “letra”; sirven para mapear las acciones a las vistas anteriores.

Referencias de código:

```103:155:app/letters/letters_service.py
# Dominio to_accept y filtrado por l10n_latam_boe_number
```

```126:205:scripts/investigation/investigate_letters_model.py
# Búsqueda de modelos, campos y vistas que contienen 'letter' o 'boe'
```

```52:66:scripts/investigation/test_letters_endpoint.py
# Dominio de prueba directo sobre account.move para letras numeradas
```

---

## 🧩 Componentes de aplicación que usan el modelo

- **Endpoints Flask (`letters.routes`):** `/to-accept`, `/to-recover`, `/in-bank`, `/send-acceptance`, `/send-recover`, `/send-bank`, `/summary`. Orquestan llamadas a `LettersService` y agrupan correos por cliente.
- **Servicio de dominio (`LettersService`):** arma el dataset de letras (valores M2O, moneda, facturas relacionadas) y calcula `status_calc`.
- **Repositorio Odoo (`OdooRepository`):** wrapper XML-RPC para `search_read`, `read`, `execute_kw`.
- **Front (plantillas Jinja):** `letters/manage.html` consume `/to-accept` y permite enviar correos; `letters/dashboard.html` consume `/summary` para KPIs y gráficos.
- **Scripts de investigación (carpeta `scripts/investigation`):**
  - `investigate_letters_model.py` y `simple_investigate.py`: listan campos de `account.move` y localizan campos relacionados a letras.
  - `investigate_bill_form.py`: inspecciona `account.bill.form` y muestra registros ejemplo.
  - `test_letters_endpoint.py`: ejecuta el endpoint `/to-accept` y consulta directa al modelo.
  - `trace_document_flow.py`: traza Planilla → Factura → Pedido → Letras.

Referencias de código:

```37:194:app/letters/routes.py
# Endpoints y agrupación de correos por cliente/aceptante
```

```421:507:app/letters/letters_service.py
# KPI y dashboard de letras
```

```219:352:app/templates/letters/manage.html
# Consumo de /letters/to-accept y rendering de la tabla en UI
```

```151:239:app/templates/letters/dashboard.html
# Consumo de /letters/summary para KPIs y gráficos ECharts
```

---

## 🖼️ Vistas Structurizr específicas de Letras

Se añadieron vistas nuevas en `docs/c4model/workspace.dsl` para cubrir el dominio de Letras con múltiples “imágenes” (C1, C2, C3 y flujo dinámico):

1. **Contexto (existente):** `systemContext financeSystem "Contexto"`  
2. **Contenedores (nuevo):** `container financeSystem "Letras - Contenedores"`  
3. **Componentes API (nuevo):** `component lettersApi "Letras - Componentes API"`  
4. **Flujo dinámico (nuevo):** `dynamic "FlujoLetrasToAccept"`  

### Cómo exportar los diagramas a PNG/SVG

```bash
# Requiere structurizr-cli en el PATH
structurizr export \
  -workspace docs/c4model/workspace.dsl \
  -format png \
  -output docs/c4model/img
```

Los archivos generados (`Contexto.png`, `Letras - Contenedores.png`, `Letras - Componentes API.png`, `FlujoLetrasToAccept.png`) pueden incrustarse en presentaciones o en MkDocs.

### Vistas en línea (render por plugin Structurizr)

```structurizr
!include workspace.dsl
!view systemContext
```

```structurizr
!include workspace.dsl
!view container "Letras - Contenedores"
```

```structurizr
!include workspace.dsl
!view component "Letras - Componentes API"
```

```structurizr
!include workspace.dsl
!view dynamic "FlujoLetrasToAccept"
```

---

## ✅ Pendientes recomendados

- Ejecutar los scripts de investigación contra Odoo para capturar ejemplos reales de vistas (`ir.ui.view`) y estados, y adjuntar capturas de los diagramas exportados.
- Si aparecen modelos alternativos (`agr.bill.form`, `account.letter`, etc.), documentar sus campos y relaciones reales en este mismo archivo.

