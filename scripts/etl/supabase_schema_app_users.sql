-- =============================================================================
-- Finanzas AGV - Catálogo de usuarios de la aplicación (RBAC)
-- =============================================================================
-- Fuente de verdad para altas/bajas y roles: admin | app_assistant | user.
-- Login: dominio corporativo + fila activa en app_users (fallback ALLOWED_USERS).
-- Rol admin vía UI nunca: solo override ADMIN_EMAILS en config/env.
--
-- Escritura/lectura vía Flask con SUPABASE_KEY (service role).
-- Aplicar en SQL Editor de Supabase o MCP apply_migration. Idempotente.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.app_users (
    email TEXT PRIMARY KEY,
    display_name TEXT,
    role VARCHAR(32) NOT NULL DEFAULT 'user'
        CHECK (role IN ('admin', 'app_assistant', 'user')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_users_role ON public.app_users (role);
CREATE INDEX IF NOT EXISTS idx_app_users_is_active ON public.app_users (is_active);
CREATE INDEX IF NOT EXISTS idx_app_users_created_at ON public.app_users (created_at DESC);

COMMENT ON TABLE public.app_users IS
    'Usuarios autorizados de Finanzas AGV y roles RBAC (admin, app_assistant, user).';
COMMENT ON COLUMN public.app_users.role IS
    'Rol único: admin | app_assistant | user. ADMIN_EMAILS fuerza admin en login.';

-- Seed: José como admin bootstrap (idempotente).
INSERT INTO public.app_users (email, display_name, role, is_active, created_by)
VALUES (
    'jose.montero@agrovetmarket.com',
    'José Montero',
    'admin',
    TRUE,
    'seed'
)
ON CONFLICT (email) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    role = 'admin',
    is_active = TRUE,
    updated_at = NOW();

-- RLS: deny-by-default para anon/authenticated; Flask service role bypasa RLS.
ALTER TABLE public.app_users ENABLE ROW LEVEL SECURITY;
