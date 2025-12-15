-- ============================================================================
-- ESQUEMA DE DATOS ANALÍTICOS - FINANZAS AGV (VERSION SIMPLIFICADA)
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
