-- ============================================================================
-- ESQUEMA DE DATOS ANALÍTICOS PARA REPORTES NETEADOS - FINANZAS AGV
-- Soporta: Matching Backwards, Diferencia de Cambio y Agrupación por Factura
-- ============================================================================

-- 1. TABLA DE SOCIOS (Ya existente, añadimos campos si faltan)
CREATE TABLE IF NOT EXISTS dim_partners (
    id BIGINT PRIMARY KEY,
    name TEXT,
    vat TEXT,
    state_name TEXT,
    is_company BOOLEAN,
    email TEXT,
    phone TEXT,
    supplier_rank INTEGER DEFAULT 0,
    customer_rank INTEGER DEFAULT 0,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. TABLA DE MOVIMIENTOS (Cabecera)
CREATE TABLE IF NOT EXISTS fact_moves (
    id BIGINT PRIMARY KEY,
    name TEXT,
    ref TEXT,
    date DATE,
    invoice_date DATE,
    invoice_date_due DATE,
    state TEXT,
    move_type TEXT,
    payment_state TEXT,
    currency_id INTEGER,
    amount_total NUMERIC(15,2),
    amount_residual NUMERIC(15,2),
    partner_id BIGINT REFERENCES dim_partners(id),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABLA DE LÍNEAS DE MOVIMIENTO (Crucial para Neteado)
CREATE TABLE IF NOT EXISTS fact_move_lines (
    id BIGINT PRIMARY KEY,
    move_id BIGINT REFERENCES fact_moves(id),
    partner_id BIGINT REFERENCES dim_partners(id),
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

-- 4. TABLA DE CONCILIACIONES PARCIALES (El corazón del Matching)
CREATE TABLE IF NOT EXISTS fact_partial_reconciles (
    id BIGINT PRIMARY KEY,
    debit_move_line_id BIGINT REFERENCES fact_move_lines(id),
    credit_move_line_id BIGINT REFERENCES fact_move_lines(id),
    amount NUMERIC(15,2),
    amount_currency NUMERIC(15,2),
    currency_id INTEGER,
    max_date DATE,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- VISTAS PARA REPORTES NETEADOS
-- ============================================================================

-- VISTA: MAPEO DE RELACIONES (Línea <-> Master Factura)
-- Esta vista identifica qué líneas (pagos/ajustes) pertenecen a qué factura master
CREATE OR REPLACE VIEW view_aml_master_mapping AS
WITH RECURSIVE reconciliation_tree AS (
    -- Caso base: Las facturas son sus propios masters
    SELECT 
        aml.id as line_id,
        aml.move_id as master_move_id,
        m.name as master_name,
        m.move_type as master_type
    FROM fact_move_lines aml
    JOIN fact_moves m ON aml.move_id = m.id
    WHERE m.move_type IN ('in_invoice', 'out_invoice')

    UNION

    -- Paso recursivo: Buscar líneas conciliadas con el master
    SELECT 
        CASE 
            WHEN apr.debit_move_line_id = rt.line_id THEN apr.credit_move_line_id
            ELSE apr.debit_move_line_id
        END as line_id,
        rt.master_move_id,
        rt.master_name,
        rt.master_type
    FROM reconciliation_tree rt
    JOIN fact_partial_reconciles apr ON (apr.debit_move_line_id = rt.line_id OR apr.credit_move_line_id = rt.line_id)
)
SELECT DISTINCT * FROM reconciliation_tree;

-- VISTA: REPORTE 42 NETEADO (Cuentas por Pagar)
CREATE OR REPLACE VIEW view_treasury_netted_report AS
SELECT 
    p.name as supplier_name,
    p.vat as supplier_vat,
    m.name as invoice_name,
    m.ref as invoice_ref,
    m.invoice_date as date_emitted,
    m.invoice_date_due as date_due,
    m.amount_total as original_amount,
    -- Saldo real agrupando pagos y diferencias de cambio
    SUM(aml.debit - aml.credit) as actual_balance,
    -- Identificar si hay diferencia de cambio
    SUM(CASE WHEN aml.account_code LIKE '67%' OR aml.account_code LIKE '77%' THEN (aml.debit - aml.credit) ELSE 0 END) as exchange_diff_amount,
    m.payment_state as odoo_payment_state
FROM fact_moves m
JOIN dim_partners p ON m.partner_id = p.id
JOIN view_aml_master_mapping vmm ON m.id = vmm.master_move_id
JOIN fact_move_lines aml ON vmm.line_id = aml.id
WHERE m.move_type = 'in_invoice'
GROUP BY p.name, p.vat, m.name, m.ref, m.invoice_date, m.invoice_date_due, m.amount_total, m.payment_state;

-- ============================================================================
-- RLS (Row Level Security) [NUEVO - agregado en la sesión de reactivación de Supabase]
-- ============================================================================
-- fact_move_lines y fact_partial_reconciles son datos analíticos de conciliación de
-- cuentas: hoy ningún cliente con ANON KEY los consulta directamente (solo el backend, vía
-- SERVICE ROLE KEY, que bypassa RLS, a través de las vistas view_aml_master_mapping y
-- view_treasury_netted_report en app/treasury/services.py). Se activa RLS con
-- "deny by default" (sin políticas) para que ningún cliente anon pueda leerlos ni
-- escribirlos directamente.
ALTER TABLE fact_move_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE fact_partial_reconciles ENABLE ROW LEVEL SECURITY;

-- Nota sobre las vistas (view_aml_master_mapping, view_treasury_netted_report): las vistas
-- de Postgres no tienen RLS propio; heredan los permisos de quien las creó a menos que se
-- marquen con `security_invoker`. Como solo se consultan desde el backend con la SERVICE
-- ROLE KEY (bypassa RLS de todas formas), no se requiere ajuste adicional mientras no se
-- exponga ninguna de las dos vistas al frontend con la ANON KEY.

