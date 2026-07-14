-- =============================================================================
-- Finanzas AGV - Tabla de estado del ETL incremental (proyecto Supabase nuevo)
-- =============================================================================
-- Soporta la sincronización incremental de scripts/etl/etl_sync_threading.py:
-- antes de cada sync se lee el último timestamp exitoso por modelo Odoo
-- (get_last_sync), y al terminar se actualiza (set_last_sync).
--
-- Aplicar DESPUÉS de scripts/etl/supabase_schema_full.sql (mismo mecanismo: MCP nuevo,
-- SQL Editor del dashboard, o `supabase db push`). Idempotente.
--
-- NOTA: supabase_schema_full.sql YA incluye esta misma tabla (CREATE TABLE IF NOT EXISTS),
-- así que aplicar ambos archivos es seguro pero redundante. Este archivo queda como
-- referencia independiente por si se prefiere aplicar solo la parte incremental sin tocar
-- el resto del esquema (p.ej. en un proyecto Supabase donde las demás tablas ya existen).
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.etl_sync_state (
    model_name      text PRIMARY KEY,   -- p.ej. 'account.move.invoices', 'account.move.letters'
    last_synced_at  timestamptz         -- NULL = nunca sincronizado (primer sync trae todo el histórico)
);

COMMENT ON TABLE public.etl_sync_state IS 'Marca de agua (watermark) por modelo Odoo para la sincronización incremental del ETL.';

-- RLS: esta tabla es uso interno exclusivo del ETL (Celery worker con SERVICE ROLE KEY,
-- que bypassa RLS). Deny-by-default para anon/authenticated: se activa RLS y no se crea
-- ninguna política, por lo que ningún cliente con ANON KEY puede leer ni escribir aquí.
ALTER TABLE public.etl_sync_state ENABLE ROW LEVEL SECURITY;
