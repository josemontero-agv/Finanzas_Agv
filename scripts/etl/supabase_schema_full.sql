-- ============================================================================
-- ESQUEMA DE DATOS ANALÍTICOS - FINANZAS AGV (VERSION SIMPLIFICADA)
-- Ejecutar este script en el Editor SQL de Supabase (proyecto NUEVO: hkthitfwqyfqfhcirvnz)
-- ============================================================================
-- Este archivo ya existía en el repo (git history) con el esquema base. Se agregó en esta
-- sesión (sin tocar las tablas/columnas/vistas originales):
--   1) RLS (Row Level Security), que hoy no estaba activado en ninguna tabla.
--   2) La tabla `rel_letter_moves` (letter_id, move_id): el ETL actual
--      (scripts/etl/etl_sync_threading.py::sync_letters) escribe directamente esta relación
--      letra <-> factura leyendo el campo 'bill_form_invoices' de account.move, sin pasar
--      por fact_bill_forms/rel_bill_form_invoices (el modelo de "planillas" definido más
--      abajo). Sin esta tabla el ETL fallaría al hacer upsert. Si en algún momento se decide
--      usar el modelo de planillas (fact_bill_forms) en vez de la relación directa, habrá
--      que actualizar también el ETL para poblar bill_form_id / rel_bill_form_invoices.
-- ============================================================================

-- 1. TABLA DE SOCIOS (Clientes y Proveedores)
CREATE TABLE IF NOT EXISTS dim_partners (
    id BIGINT PRIMARY KEY,
    name TEXT,
    vat TEXT, -- RUC/DNI
    country_code TEXT,
    state_name TEXT, -- Provincia/Departamento
    is_company BOOLEAN,
    email TEXT,
    phone TEXT,
    supplier_rank INTEGER DEFAULT 0,
    customer_rank INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TABLA DE MOVIMIENTOS (Facturas y Notas de Crédito)
CREATE TABLE IF NOT EXISTS fact_moves (
    id BIGINT PRIMARY KEY,
    name TEXT, -- Número de documento (Ej: F001-0001)
    ref TEXT,
    date DATE, -- Fecha contable
    invoice_date DATE, -- Fecha de emisión
    invoice_date_due DATE, -- Fecha vencimiento
    state TEXT, -- posted, draft, cancel
    move_type TEXT, -- out_invoice, out_refund, in_invoice, in_refund
    payment_state TEXT, -- paid, not_paid, partial
    invoice_origin TEXT, -- Referencia al pedido (ej: S00123)

    -- Montos
    currency_id INTEGER,
    amount_total NUMERIC(15,2),
    amount_residual NUMERIC(15,2),
    amount_untaxed NUMERIC(15,2),

    -- Relaciones
    partner_id BIGINT REFERENCES dim_partners(id),
    reversed_entry_id INTEGER, -- ID de la factura original (si es Nota de Crédito)

    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABLA DE PLANILLAS DE LETRAS (Bill Forms)
CREATE TABLE IF NOT EXISTS fact_bill_forms (
    id BIGINT PRIMARY KEY,
    name TEXT, -- FLC-0001
    state TEXT,
    amount_total NUMERIC(15,2),
    partner_id BIGINT REFERENCES dim_partners(id),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. TABLA DE LETRAS (Bills of Exchange)
CREATE TABLE IF NOT EXISTS fact_letters (
    id BIGINT PRIMARY KEY,
    name TEXT, -- Nombre interno (Ej: RCB1/2025/...)
    boe_number TEXT, -- Número de la letra (Ej: 6732/25)
    state TEXT, -- portfolio, to_accept, etc.
    date DATE,
    due_date DATE,
    amount_total NUMERIC(15,2),
    partner_id BIGINT REFERENCES dim_partners(id),
    move_type TEXT, -- in_bill (generalmente para letras)
    bill_form_id BIGINT REFERENCES fact_bill_forms(id), -- Enlace a la planilla
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. TABLA DE UNIÓN (Planilla <-> Facturas)
-- Una planilla agrupa varias facturas
CREATE TABLE IF NOT EXISTS rel_bill_form_invoices (
    bill_form_id BIGINT REFERENCES fact_bill_forms(id),
    move_id BIGINT REFERENCES fact_moves(id),
    PRIMARY KEY (bill_form_id, move_id)
);

-- 6. TABLA DE UNIÓN (Letra <-> Facturas) [NUEVA - ver nota al inicio del archivo]
-- Usada directamente por el ETL actual (sync_letters), leyendo 'bill_form_invoices' de la
-- letra en Odoo y relacionándola 1:N con las facturas agrupadas, sin pasar por fact_bill_forms.
CREATE TABLE IF NOT EXISTS rel_letter_moves (
    letter_id BIGINT REFERENCES fact_letters(id) ON DELETE CASCADE,
    move_id BIGINT REFERENCES fact_moves(id) ON DELETE CASCADE,
    PRIMARY KEY (letter_id, move_id)
);

-- 7. TABLA DE ESTADO DEL ETL INCREMENTAL [NUEVA]
-- Ver también scripts/etl/supabase_schema_etl_state.sql (archivo dedicado, mismo contenido).
CREATE TABLE IF NOT EXISTS etl_sync_state (
    model_name TEXT PRIMARY KEY,
    last_synced_at TIMESTAMPTZ
);

-- ============================================================================
-- VISTAS ANALÍTICAS
-- ============================================================================

-- VISTA: TRAZABILIDAD COMPLETA (Factura -> Planilla -> Letra)
CREATE OR REPLACE VIEW view_document_traceability AS
SELECT 
    p.name AS partner_name,
    m.invoice_origin AS order_name, -- Usamos el campo directo de la factura
    m.name AS invoice_name,
    m.amount_total AS invoice_amount,
    bf.name AS bill_form_name,
    l.name AS letter_internal,
    l.boe_number AS letter_number,
    l.amount_total AS letter_amount,
    l.due_date AS letter_due_date,
    l.state AS letter_state
FROM fact_moves m
LEFT JOIN dim_partners p ON m.partner_id = p.id
-- Join con Planillas a través de la tabla de relación
LEFT JOIN rel_bill_form_invoices rbfi ON m.id = rbfi.move_id
LEFT JOIN fact_bill_forms bf ON rbfi.bill_form_id = bf.id
-- Join con Letras
LEFT JOIN fact_letters l ON bf.id = l.bill_form_id
WHERE m.move_type = 'out_invoice';

-- ============================================================================
-- RLS (Row Level Security) [NUEVO - ninguna de estas tablas tenía RLS activado]
-- ============================================================================
-- El ETL (scripts/etl/etl_sync_threading.py) escribe con la SERVICE ROLE KEY, que
-- bypassa RLS siempre. Estas políticas solo afectan a clientes con la ANON KEY.
-- Solo se habilita SELECT para anon/authenticated en las tablas que el frontend consulta
-- directamente hoy (frontend/lib/supabase.ts, frontend/app/diagnostics/page.tsx):
-- dim_partners, fact_moves, fact_letters. El resto queda en "deny by default"
-- (RLS activado sin políticas) hasta que haya un consumidor directo con ANON KEY.

ALTER TABLE dim_partners ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_moves ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_bill_forms ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_letters ENABLE ROW LEVEL SECURITY;
ALTER TABLE rel_bill_form_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE rel_letter_moves ENABLE ROW LEVEL SECURITY;
ALTER TABLE etl_sync_state ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "dim_partners_select_anon" ON dim_partners;
CREATE POLICY "dim_partners_select_anon"
    ON dim_partners FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "fact_moves_select_anon" ON fact_moves;
CREATE POLICY "fact_moves_select_anon"
    ON fact_moves FOR SELECT
    TO anon, authenticated
    USING (true);

DROP POLICY IF EXISTS "fact_letters_select_anon" ON fact_letters;
CREATE POLICY "fact_letters_select_anon"
    ON fact_letters FOR SELECT
    TO anon, authenticated
    USING (true);

-- fact_bill_forms, rel_bill_form_invoices, rel_letter_moves y etl_sync_state quedan sin
-- políticas (deny by default): ni el frontend ni ningún cliente anon las consulta hoy.
-- Si en el futuro el frontend necesita leer alguna directamente, agregar aquí una política
-- de SELECT análoga a las anteriores.
