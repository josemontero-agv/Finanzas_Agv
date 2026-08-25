-- =============================================================================
-- Finanzas AGV - Tabla de actividad de usuarios (product analytics v1)
-- =============================================================================
-- Persistencia de logins, logout y page_views para el tablero /observability.
-- Escritura exclusiva desde Flask con SUPABASE_KEY (service role).
--
-- Aplicar en el SQL Editor de Supabase (o vía MCP apply_migration). Idempotente.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.user_activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT NOT NULL,
    username TEXT,
    event_category VARCHAR(50) NOT NULL,
    event_name VARCHAR(100) NOT NULL,
    payload JSONB DEFAULT '{}'::jsonb,
    path VARCHAR(255),
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ual_created_at ON public.user_activity_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ual_event_name ON public.user_activity_logs (event_name);
CREATE INDEX IF NOT EXISTS idx_ual_user_email ON public.user_activity_logs (user_email);
CREATE INDEX IF NOT EXISTS idx_ual_event_created ON public.user_activity_logs (event_name, created_at DESC);

COMMENT ON TABLE public.user_activity_logs IS
    'Eventos de uso de la app (auth + nav) para el tablero Observabilidad (solo admins).';

-- RLS: escritura/lectura vía service role desde Flask (bypass RLS).
-- Deny-by-default para anon/authenticated: sin políticas, el cliente no puede insertar ni leer.
ALTER TABLE public.user_activity_logs ENABLE ROW LEVEL SECURITY;
