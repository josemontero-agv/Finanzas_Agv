-- ============================================================================
-- ESQUEMA DE DATOS ANALÍTICOS - FINANZAS AGV
-- Ejecutar este script en el Editor SQL de Supabase
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
-- Almacena tanto Cobranzas (out_*) como Tesorería (in_*)
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
    
    -- Montos
    currency_id INTEGER,
    amount_total NUMERIC(15,2),
    amount_residual NUMERIC(15,2),
    amount_untaxed NUMERIC(15,2),
    
    -- Relaciones
    partner_id BIGINT REFERENCES dim_partners(id),
    reversed_entry_id INTEGER, -- ID de la factura original (si es Nota de Crédito)
    
    -- Metadatos
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TABLA DE LETRAS (Bills of Exchange)
CREATE TABLE IF NOT EXISTS fact_letters (
    id BIGINT PRIMARY KEY,
    name TEXT, -- Nombre interno (Ej: RCB1/2025/...)
    boe_number TEXT, -- Número de la letra (Ej: 6732/25)
    state TEXT, -- portfolio, etc.
    date DATE,
    due_date DATE,
    amount_total NUMERIC(15,2),
    partner_id BIGINT REFERENCES dim_partners(id),
    move_type TEXT, -- in_bill (generalmente para letras)
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. TABLA DE UNIÓN (Letras <-> Facturas)
-- Esta es la tabla mágica que resuelve tu problema de joins
CREATE TABLE IF NOT EXISTS rel_letter_moves (
    letter_id BIGINT REFERENCES fact_letters(id),
    move_id BIGINT REFERENCES fact_moves(id),
    PRIMARY KEY (letter_id, move_id)
);

-- ============================================================================
-- VISTAS ANALÍTICAS (Para usar desde Flask/Pandas)
-- ============================================================================

-- VISTA: REPORTE DE COBRANZAS (Cuenta 12 + Letras)
CREATE OR REPLACE VIEW view_collections_analytics AS
SELECT 
    m.id AS move_id,
    m.name AS document_number,
    m.invoice_date,
    m.invoice_date_due,
    m.amount_total,
    m.amount_residual,
    m.state AS status,
    m.move_type,
    p.name AS customer_name,
    p.vat AS customer_ruc,
    -- Información de Letra (si existe asociada)
    l.boe_number AS letter_number,
    l.state AS letter_state
FROM fact_moves m
JOIN dim_partners p ON m.partner_id = p.id
LEFT JOIN rel_letter_moves rlm ON m.id = rlm.move_id
LEFT JOIN fact_letters l ON rlm.letter_id = l.id
WHERE m.move_type IN ('out_invoice', 'out_refund');

-- VISTA: REPORTE DE TESORERÍA (Cuenta 42 + Notas Crédito)
CREATE OR REPLACE VIEW view_treasury_analytics AS
SELECT 
    m.id AS move_id,
    m.name AS document_number,
    m.invoice_date,
    m.amount_total,
    m.move_type,
    p.name AS supplier_name,
    p.vat AS supplier_ruc,
    -- Nota de Crédito lógica
    CASE 
        WHEN m.move_type = 'in_refund' THEN 'Nota de Crédito' 
        ELSE 'Factura' 
    END AS doc_type
FROM fact_moves m
JOIN dim_partners p ON m.partner_id = p.id
WHERE m.move_type IN ('in_invoice', 'in_refund');

