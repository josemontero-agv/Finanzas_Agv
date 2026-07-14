-- ============================================================================
-- ESQUEMA SUPABASE — PILOTO COBRANZAS (Fase 3, Odoo -> Supabase)
-- ============================================================================
-- Este archivo NO modifica supabase_schema_full.sql ni supabase_schema_netted.sql;
-- solo agrega columnas nuevas (ALTER TABLE ... ADD COLUMN IF NOT EXISTS) y tablas
-- nuevas (CREATE TABLE IF NOT EXISTS), por lo que es seguro aplicarlo después de
-- esos dos archivos en cualquier orden relativo entre sí, y es re-ejecutable.
--
-- Contexto importante: `fact_move_lines` y `fact_partial_reconciles` ya están
-- declaradas en supabase_schema_netted.sql, pero a la fecha de este cambio no las
-- puebla ningún proceso (Tesorería usa vistas/consultas propias vía
-- app/core/supabase.py, no estas tablas). Por eso aquí se reutilizan esas mismas
-- tablas/columnas para el piloto de Cobranzas en vez de crear tablas paralelas:
-- se agregan solo las columnas que le faltan (parent_state, matched_debit_ids,
-- matched_credit_ids, currency_name) para poder reproducir
-- app/collections/services.py::get_report_lines.
--
-- Grano de datos: account.move.line de las cuentas 12x usadas en Cobranzas
-- (ver CollectionsService._parse_account_codes: 122, 1212, 123, 1312, 132, 13).
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. fact_move_lines — ampliar tabla existente (definida en supabase_schema_netted.sql)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_move_lines (
    id BIGINT PRIMARY KEY,
    move_id BIGINT,
    partner_id BIGINT,
    account_id INTEGER,
    account_code TEXT,
    name TEXT,
    date DATE,
    date_maturity DATE,
    debit NUMERIC(15,2) DEFAULT 0,
    credit NUMERIC(15,2) DEFAULT 0,
    balance NUMERIC(15,2) DEFAULT 0,
    amount_residual NUMERIC(15,2) DEFAULT 0,
    amount_currency NUMERIC(15,2) DEFAULT 0,
    currency_id INTEGER,
    reconciled BOOLEAN DEFAULT FALSE,
    full_reconcile_id INTEGER,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Campos que necesita Cobranzas y que netted.sql no incluía:
ALTER TABLE fact_move_lines ADD COLUMN IF NOT EXISTS parent_state TEXT;
ALTER TABLE fact_move_lines ADD COLUMN IF NOT EXISTS matched_debit_ids JSONB DEFAULT '[]'::jsonb;
ALTER TABLE fact_move_lines ADD COLUMN IF NOT EXISTS matched_credit_ids JSONB DEFAULT '[]'::jsonb;
ALTER TABLE fact_move_lines ADD COLUMN IF NOT EXISTS currency_name TEXT;

-- ----------------------------------------------------------------------------
-- 2. fact_partial_reconciles — ya tiene todo lo que Cobranzas necesita
--    (id, debit_move_line_id, credit_move_line_id, amount, max_date). Se
--    re-declara aquí (idempotente) por si este archivo se aplica solo, sin
--    haber corrido antes supabase_schema_netted.sql.
--    Nota: pese al nombre "debit_move_id/credit_move_id" en Odoo
--    (account.partial.reconcile), esos campos apuntan a account.move.line, por
--    lo que "debit_move_line_id"/"credit_move_line_id" (nombres ya usados en
--    netted.sql) son semánticamente correctos y se conservan sin cambios.
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_partial_reconciles (
    id BIGINT PRIMARY KEY,
    debit_move_line_id BIGINT,
    credit_move_line_id BIGINT,
    amount NUMERIC(15,2),
    amount_currency NUMERIC(15,2),
    currency_id INTEGER,
    max_date DATE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. fact_moves — ampliar tabla existente (supabase_schema_full.sql / netted.sql)
--    con los campos de cabecera de factura que usa get_report_lines.
-- ----------------------------------------------------------------------------
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS ref TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS invoice_origin TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS bill_form_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS l10n_latam_document_type_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS l10n_latam_boe_number TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS sales_channel_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS sale_type_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS sale_type_name TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS team_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS team_name TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS order_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS amount_residual_with_retention NUMERIC(15,2);
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS amount_residual_signed NUMERIC(15,2);
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS invoice_payment_term_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS invoice_payment_term_name TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS invoice_user_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS invoice_user_name TEXT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS currency_name TEXT;
-- Campo custom de Odoo usado en services.py para "línea comercial" (ver
-- CollectionsService.get_report_lines: bill_form_invoices_order_sales_line_commercial_zone_id).
-- Se guarda también el nombre resuelto porque no hay dimensión propia para él.
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS bill_form_invoices_order_sales_line_commercial_zone_id BIGINT;
ALTER TABLE IF EXISTS fact_moves ADD COLUMN IF NOT EXISTS commercial_zone_name TEXT;

-- ----------------------------------------------------------------------------
-- 3.b dim_partners — ampliar tabla existente (supabase_schema_full.sql /
--     netted.sql). `country_code` ya existía en el esquema pero ningún sync lo
--     poblaba (sync_partners solo leía country_id para el nombre de provincia);
--     se aprovecha para agregar también el distrito y el nombre de país que
--     usa get_report_lines (partner_district, partner_country_name).
-- ----------------------------------------------------------------------------
ALTER TABLE IF EXISTS dim_partners ADD COLUMN IF NOT EXISTS l10n_pe_district TEXT;
ALTER TABLE IF EXISTS dim_partners ADD COLUMN IF NOT EXISTS country_name TEXT;

-- ----------------------------------------------------------------------------
-- 4. Dimensiones nuevas
-- ----------------------------------------------------------------------------

-- Catálogo de cuentas contables (account.account)
CREATE TABLE IF NOT EXISTS dim_accounts (
    id BIGINT PRIMARY KEY,
    code TEXT,
    name TEXT,
    currency_name TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Catálogo de canales de venta (agr.sales.channel)
CREATE TABLE IF NOT EXISTS dim_sales_channels (
    id BIGINT PRIMARY KEY,
    name TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Catálogo de tipos de documento LATAM (l10n_latam.document.type)
CREATE TABLE IF NOT EXISTS dim_doc_types (
    id BIGINT PRIMARY KEY,
    name TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Mapeo cliente de crédito -> sub canal / grupos comerciales (agr.credit.customer).
-- Simplificación deliberada: en vez de replicar agr.groups como dimensión aparte,
-- el ETL resuelve los nombres de grupo en el momento del sync y los guarda ya
-- concatenados (mismo formato que hoy arma CollectionsService.get_report_lines
-- vía partner_groups_map), evitando un join adicional en cada request.
CREATE TABLE IF NOT EXISTS dim_credit_customers (
    partner_id BIGINT PRIMARY KEY,
    sub_channel_name TEXT,
    partner_groups_display TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Órdenes de venta (sale.order): sub_channel_id -> sub canal, tag_ids -> método de pago.
-- Misma simplificación que dim_credit_customers: se guarda tag_ids (para poder
-- filtrar por ID de etiqueta, igual que hoy `payment_method` filtra por ID de
-- crm.tag) y además el nombre ya resuelto y concatenado para mostrar en pantalla
-- sin otro join.
CREATE TABLE IF NOT EXISTS dim_sale_orders (
    id BIGINT PRIMARY KEY,
    sub_channel_name TEXT,
    tag_ids JSONB DEFAULT '[]'::jsonb,
    payment_method_display TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Etiquetas (crm.tag) usadas como "método de pago" en sale.order.tag_ids.
-- Catálogo mínimo (id, name) para poder reconstruir la lista de opciones de
-- filtro (get_filter_options -> payment_methods) sin tener que desconcatenar
-- dim_sale_orders.payment_method_display.
CREATE TABLE IF NOT EXISTS dim_payment_tags (
    id BIGINT PRIMARY KEY,
    name TEXT,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 5. Índices
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_move_lines_move_id ON fact_move_lines(move_id);
CREATE INDEX IF NOT EXISTS idx_fact_move_lines_partner_id ON fact_move_lines(partner_id);
CREATE INDEX IF NOT EXISTS idx_fact_move_lines_account_id ON fact_move_lines(account_id);
CREATE INDEX IF NOT EXISTS idx_fact_move_lines_date ON fact_move_lines(date);
CREATE INDEX IF NOT EXISTS idx_fact_move_lines_date_maturity ON fact_move_lines(date_maturity);
CREATE INDEX IF NOT EXISTS idx_fact_move_lines_account_code ON fact_move_lines(account_code);

CREATE INDEX IF NOT EXISTS idx_fact_partial_reconciles_debit_line ON fact_partial_reconciles(debit_move_line_id);
CREATE INDEX IF NOT EXISTS idx_fact_partial_reconciles_credit_line ON fact_partial_reconciles(credit_move_line_id);
CREATE INDEX IF NOT EXISTS idx_fact_partial_reconciles_max_date ON fact_partial_reconciles(max_date);

CREATE INDEX IF NOT EXISTS idx_fact_moves_order_id ON fact_moves(order_id);
CREATE INDEX IF NOT EXISTS idx_fact_moves_bill_form_id ON fact_moves(bill_form_id);
CREATE INDEX IF NOT EXISTS idx_fact_moves_sales_channel_id ON fact_moves(sales_channel_id);
CREATE INDEX IF NOT EXISTS idx_fact_moves_doc_type_id ON fact_moves(l10n_latam_document_type_id);
CREATE INDEX IF NOT EXISTS idx_fact_moves_boe_number ON fact_moves(l10n_latam_boe_number);

-- ----------------------------------------------------------------------------
-- 6. RLS (Row Level Security) — mismo patrón de supabase_schema_full.sql
-- ----------------------------------------------------------------------------
-- El backend Flask y el ETL usan siempre la SERVICE ROLE KEY (bypassa RLS). Se
-- otorga SELECT a anon/authenticated por consistencia con el patrón ya usado en
-- supabase_schema_full.sql, aunque hoy el frontend no consulta estas tablas
-- directamente (solo lo hace vía Flask). Si esto no es deseable por exponer
-- datos financieros de línea con la ANON KEY, restringir a "deny by default"
-- (como se dejó `fact_move_lines`/`fact_partial_reconciles` en netted.sql).

ALTER TABLE fact_move_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_partial_reconciles ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_sales_channels ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_doc_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_credit_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_sale_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE dim_payment_tags ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "fact_move_lines_select_anon" ON fact_move_lines;
CREATE POLICY "fact_move_lines_select_anon"
    ON fact_move_lines FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "fact_partial_reconciles_select_anon" ON fact_partial_reconciles;
CREATE POLICY "fact_partial_reconciles_select_anon"
    ON fact_partial_reconciles FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "dim_accounts_select_anon" ON dim_accounts;
CREATE POLICY "dim_accounts_select_anon"
    ON dim_accounts FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "dim_sales_channels_select_anon" ON dim_sales_channels;
CREATE POLICY "dim_sales_channels_select_anon"
    ON dim_sales_channels FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "dim_doc_types_select_anon" ON dim_doc_types;
CREATE POLICY "dim_doc_types_select_anon"
    ON dim_doc_types FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "dim_credit_customers_select_anon" ON dim_credit_customers;
CREATE POLICY "dim_credit_customers_select_anon"
    ON dim_credit_customers FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "dim_sale_orders_select_anon" ON dim_sale_orders;
CREATE POLICY "dim_sale_orders_select_anon"
    ON dim_sale_orders FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "dim_payment_tags_select_anon" ON dim_payment_tags;
CREATE POLICY "dim_payment_tags_select_anon"
    ON dim_payment_tags FOR SELECT
    TO anon, authenticated
    USING (true);

-- ----------------------------------------------------------------------------
-- 7. Watermarks del ETL incremental
-- ----------------------------------------------------------------------------
-- No se crea tabla nueva: se reutiliza `etl_sync_state` (ver
-- scripts/etl/supabase_schema_etl_state.sql). Las claves lógicas nuevas que usa
-- scripts/etl/etl_sync_threading.py para este dominio son:
--   'account.move.line.collections', 'account.partial.reconcile',
--   'dim.accounts', 'dim.sales_channels', 'dim.doc_types',
--   'dim.credit_customers', 'dim.sale_orders'
-- No requieren fila inicial: get_last_sync() devuelve NULL si no existen y el
-- primer sync trae el histórico completo (mismo comportamiento que sync_moves).
