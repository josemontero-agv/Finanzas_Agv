-- =============================================================================
-- Finanzas AGV - Catálogo de plataformas (Centro de aplicaciones)
-- =============================================================================
-- Inventario operativo: Finanzas AGV, Odoo y otras apps registradas vía UI.
-- Health live se resuelve en API (no se persiste estado aquí en v1).
--
-- Escritura/lectura vía Flask con SUPABASE_KEY (service role).
-- Aplicar en SQL Editor de Supabase o MCP apply_migration. Idempotente.
-- =============================================================================

CREATE TABLE IF NOT EXISTS public.app_platforms (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    base_url TEXT,
    kind VARCHAR(32) NOT NULL DEFAULT 'other'
        CHECK (kind IN ('finanzas_agv', 'odoo', 'other')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 100,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_app_platforms_kind ON public.app_platforms (kind);
CREATE INDEX IF NOT EXISTS idx_app_platforms_is_active ON public.app_platforms (is_active);
CREATE INDEX IF NOT EXISTS idx_app_platforms_sort ON public.app_platforms (sort_order, name);

COMMENT ON TABLE public.app_platforms IS
    'Catálogo de plataformas del Centro de aplicaciones (/apps).';
COMMENT ON COLUMN public.app_platforms.kind IS
    'Tipo: finanzas_agv | odoo | other. Health live solo para finanzas_agv/odoo.';

-- Seeds: Finanzas AGV + Odoo (idempotente por slug).
INSERT INTO public.app_platforms (name, slug, base_url, kind, is_active, sort_order, notes)
VALUES
    (
        'Finanzas AGV',
        'finanzas-agv',
        NULL,
        'finanzas_agv',
        TRUE,
        10,
        'Esta aplicación (Cobranzas, Tesorería, Letras).'
    ),
    (
        'Odoo ERP',
        'odoo-erp',
        NULL,
        'odoo',
        TRUE,
        20,
        'ERP corporativo Agrovet Market.'
    )
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    kind = EXCLUDED.kind,
    is_active = TRUE,
    sort_order = EXCLUDED.sort_order,
    notes = EXCLUDED.notes,
    updated_at = NOW();

ALTER TABLE public.app_platforms ENABLE ROW LEVEL SECURITY;
