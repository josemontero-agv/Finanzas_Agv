-- ====================================================================
-- PROYECTO: Ecosistema Financiero High-Performance v1.0 (Finanzas AGV)
-- DESCRIPCIÓN: DDL Base para el nodo analítico y de automatización (PostgreSQL / Supabase)
-- ====================================================================

-- 1. Tablas Maestras
-- ==========================================

-- Tabla de Contactos / Clientes / Proveedores (Replicada de Odoo)
CREATE TABLE res_partner (
    id INTEGER PRIMARY KEY, -- ID original Odoo
    name VARCHAR(255) NOT NULL,
    email VARCHAR(150),
    location_type VARCHAR(50) CHECK (location_type IN ('LIMA', 'PROVINCIA', 'OTRO')) DEFAULT 'LIMA',
    write_date TIMESTAMP NOT NULL
);

CREATE INDEX idx_partner_write ON res_partner(write_date);


-- 2. Tablas Transaccionales
-- ==========================================

-- Tabla de Facturas y Letras (Replicada de Odoo)
CREATE TABLE account_move (
    id INTEGER PRIMARY KEY, -- ID original Odoo
    partner_id INTEGER NOT NULL,
    name VARCHAR(100),
    move_type VARCHAR(50),
    state VARCHAR(50),
    invoice_date DATE,
    invoice_date_due DATE,
    amount_total NUMERIC(15, 2) DEFAULT 0.0,
    amount_residual NUMERIC(15, 2) DEFAULT 0.0,
    write_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_move_partner FOREIGN KEY (partner_id) REFERENCES res_partner(id) ON DELETE RESTRICT
);

CREATE INDEX idx_move_due_date ON account_move(invoice_date_due);
CREATE INDEX idx_move_partner ON account_move(partner_id);
CREATE INDEX idx_move_write ON account_move(write_date);

-- Tabla de Pagos aplicados a documentos (Crucial para el corte histórico)
CREATE TABLE account_payment (
    id INTEGER PRIMARY KEY, -- ID original Odoo
    move_id INTEGER NOT NULL,
    date_payment DATE NOT NULL,
    amount NUMERIC(15, 2) NOT NULL,
    write_date TIMESTAMP NOT NULL,
    CONSTRAINT fk_payment_move FOREIGN KEY (move_id) REFERENCES account_move(id) ON DELETE CASCADE
);

CREATE INDEX idx_payment_move ON account_payment(move_id);
CREATE INDEX idx_payment_date ON account_payment(date_payment);
CREATE INDEX idx_payment_write ON account_payment(write_date);


-- 3. Tablas de Auditoría y Local
-- ==========================================

-- Tabla de logs de comunicación (Para evitar envíos dobles y llevar trazabilidad)
CREATE TABLE communication_log (
    id BIGSERIAL PRIMARY KEY,
    move_id INTEGER NOT NULL,
    partner_id INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'SENT', -- SENT, FAILED, DELIVERED
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    context TEXT,
    CONSTRAINT fk_log_move FOREIGN KEY (move_id) REFERENCES account_move(id) ON DELETE CASCADE,
    CONSTRAINT fk_log_partner FOREIGN KEY (partner_id) REFERENCES res_partner(id) ON DELETE CASCADE
);

CREATE INDEX idx_log_sent_at ON communication_log(sent_at);
CREATE INDEX idx_log_move_partner_time ON communication_log(move_id, partner_id, sent_at);

-- ====================================================================
-- FUNCIONES ÚTILES / REGLAS
-- ====================================================================

-- Función para verificar si se puede enviar un email (Prevención Anti-Spam 24h)
-- Retorna BOOLEAN (TRUE = OK para enviar, FALSE = Recientemente notificado)
CREATE OR REPLACE FUNCTION can_send_notification(p_move_id INTEGER, p_partner_id INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    recent_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO recent_count
    FROM communication_log
    WHERE move_id = p_move_id
      AND partner_id = p_partner_id
      AND status = 'SENT'
      AND sent_at >= NOW() - INTERVAL '24 hours';
      
    RETURN recent_count = 0;
END;
$$ LANGUAGE plpgsql;
